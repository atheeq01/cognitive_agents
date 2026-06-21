from fastapi import APIRouter, Request, HTTPException, status
import logging
import base64
import json
import asyncio
import time

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])


# Lazy import processors to avoid crashing if optional dependencies are missing at startup
def _get_processors():
    from app.processors.document_ai_processor import document_ai_processor
    from app.processors.speech_to_text import speech_to_text_processor
    from app.processors.vision_ocr import vision_ocr_processor
    from app.ucd.section_chunker import section_chunker

    return (
        document_ai_processor,
        speech_to_text_processor,
        vision_ocr_processor,
        section_chunker,
    )

async def _trigger_project_synthesis(project_id: str):
    """
    Background task to run project-level synthesis after a document finishes.
    """
    try:
        from app.services.firestore_service import firestore_service
        from app.vector_store.pinecone_adapter import pinecone_adapter
        from app.agents.contradiction_pipeline.project_synthesis_agent import project_synthesis_agent
        
        logger.info(f"[Synthesis] Starting project synthesis for {project_id}")
        docs = await firestore_service.get_completed_documents(project_id)
        
        # Pull claims directly from the completed documents to avoid Pinecone eventual consistency delays
        all_claims = []
        for doc in docs:
            doc_claims = doc.get("results", {}).get("claims", [])
            for c in doc_claims:
                all_claims.append({
                    "fact": c.get("fact"),
                    "source_location": c.get("source_location")
                })
                
        # Fallback to Pinecone if we have no claims (e.g., from older documents before this fix)
        if not all_claims:
            all_claims = await pinecone_adapter.fetch_all(project_id, type="claim")
        
        report = await project_synthesis_agent.synthesize(project_id, docs, all_claims)
        await firestore_service.update_project_report(project_id, report)
        logger.info(f"[Synthesis] Completed project synthesis for {project_id}")
    except Exception as e:
        logger.error(f"[Synthesis] Failed project synthesis: {e}", exc_info=True)


async def _process_document(project_id: str, document_id: str, gcs_path: str):
    """
    Core processing pipeline:
    1. Download the file from GCS
    2. Route to the correct processor based on MIME type
    3. Chunk the extracted text using the UCD section chunker
    """
    from app.services.firestore_service import firestore_service

    pipeline_start = time.perf_counter()
    document_name = gcs_path.split("/")[-1] if gcs_path else "Unknown Document"
    logger.info(
        f"[Pipeline] ▶ START | project={project_id} | document={document_id} | file={document_name}"
    )
    try:
        await firestore_service.update_job_status(
            project_id,
            document_id,
            "Extracting content",
            10,
            document_name=document_name,
        )
        # Step 1: Download file bytes from GCS
        from google.cloud import storage as gcs

        loop = asyncio.get_running_loop()

        def _download():
            import os

            client = gcs.Client()
            env_bucket = os.environ.get("GCS_BUCKET_NAME", "omnimind-documents")
            return client.bucket(env_bucket).blob(gcs_path).download_as_bytes()

        try:
            gcs_start = time.perf_counter()
            logger.info(f"[Pipeline] [1/7] Downloading from GCS | path={gcs_path}")
            file_bytes = await loop.run_in_executor(None, _download)
            logger.info(
                f"[Pipeline] [1/7] GCS download DONE | "
                f"size={len(file_bytes)} bytes | elapsed={time.perf_counter()-gcs_start:.3f}s"
            )
        except Exception as e:
            logger.error(f"[Pipeline] [1/7] GCS download FAILED | path={gcs_path} | error={e}")
            raise e

        # Step 2: Determine MIME type and route to the correct processor
        doc_ai, speech_processor, vision_processor, chunker = _get_processors()

        import magic

        mime_type = (
            magic.from_buffer(file_bytes, mime=True)
            if file_bytes
            else "application/pdf"
        )

        proc_start = time.perf_counter()
        logger.info(
            f"[Pipeline] [2/7] Routing to processor | mime_type={mime_type} | document={document_id}"
        )
        if mime_type in ("image/jpeg", "image/png", "image/gif", "image/webp"):
            result = await vision_processor.process_image(file_bytes, mime_type)
        elif mime_type.startswith("audio/") or mime_type.startswith("video/"):
            result = await speech_processor.process_audio(file_bytes, mime_type)
        else:
            # Default: treat as a document (PDF, text, DOCX, etc.)
            result = await doc_ai.process_document(
                file_bytes, mime_type, gcs_path=gcs_path, document_id=document_id
            )

        raw_text = result.get("raw_text", "")
        modality = result.get("modality", "unknown")

        # Step 3: Chunk the extracted text
        pages = result.get("pages", [])
        audio_meta = result.get("audio_meta", {})
        utterances = audio_meta.get("utterances", [])
        chunks = chunker.chunk_document(raw_text, pages=pages, utterances=utterances) if raw_text else []

        logger.info(
            f"[Pipeline] [2/7] Content extracted & chunked | "
            f"modality={modality} | chunks={len(chunks)} | "
            f"text_length={len(raw_text)} chars | elapsed={time.perf_counter()-proc_start:.3f}s"
        )
        
        # Guard: if extraction yielded absolutely no text, we cannot run intelligence models.
        if not raw_text.strip():
            logger.warning(f"[Pipeline] Extraction returned empty text for {document_id}. Skipping intelligence steps.")
            await firestore_service.update_job_status(
                project_id,
                document_id,
                "Completed (No Text Extracted)",
                100,
                "completed",
                document_name=document_name,
                results={
                    "summary": "No readable text could be extracted from this document.",
                    "cognitive_insights": None,
                    "similarities": [],
                    "contradictions": [],
                    "markdown_report": f"# Document Intelligence Report: {document_name}\n\nNo readable text could be extracted from this document. Please ensure it is a valid, readable format.",
                },
            )
            return

        # Use the shared orchestrator for prototype execution

        from app.agents.pipeline import orchestrator
        from app.services.report_generator import report_generator

        # 4. Per-chunk analysis (Phase 1)
        await firestore_service.update_job_status(
            project_id, document_id, "Running cognitive analysis", 30
        )
        all_claims = []
        doc_summaries = []
        chunk_start = time.perf_counter()
        logger.info(
            f"[Pipeline] [3/7] Starting per-chunk analysis | "
            f"chunks={len(chunks)} | project={project_id} | document={document_id}"
        )

        sem = asyncio.Semaphore(2)

        async def process_chunk_with_sem(idx, chunk):
            async with sem:
                chunk_text = chunk.get("text", "") if isinstance(chunk, dict) else chunk
                page_number = chunk.get("page_number") if isinstance(chunk, dict) else None
                timestamp_start = chunk.get("timestamp_start_seconds") if isinstance(chunk, dict) else None
                speaker_id = chunk.get("speaker_id") if isinstance(chunk, dict) else None
                logger.info(
                    f"[Pipeline] [3/7] Processing chunk {idx+1}/{len(chunks)} | "
                    f"chunk_length={len(chunk_text)} chars"
                )
                return await orchestrator.process_chunk(
                    project_id, 
                    chunk_text,
                    metadata={
                        "document_id": document_id, 
                        "document_name": document_name, 
                        "modality": modality, 
                        "page_number": page_number,
                        "timestamp_start_seconds": timestamp_start,
                        "speaker_id": speaker_id
                    }
                )

        tasks = [process_chunk_with_sem(idx, chunk) for idx, chunk in enumerate(chunks)]
        results = await asyncio.gather(*tasks)

        for res in results:
            all_claims.extend(res.get("claims", []))
            doc_summaries.append(res.get("summary", ""))

        full_summary = " ".join(doc_summaries)
        logger.info(
            f"[Pipeline] [3/7] Per-chunk analysis DONE | "
            f"total_claims={len(all_claims)} | elapsed={time.perf_counter()-chunk_start:.3f}s"
        )

        # 5. Full Document Cognitive Analysis (Phase 1)
        cog_start = time.perf_counter()
        logger.info(
            f"[Pipeline] [4/7] Starting full-document cognitive analysis | "
            f"project={project_id} | document={document_id}"
        )
        cognitive_res = await orchestrator.process_full_document(project_id, raw_text)
        cognitive_insights = cognitive_res.get("cognitive_insights")
        logger.info(
            f"[Pipeline] [4/7] Cognitive analysis DONE | "
            f"has_insights={cognitive_insights is not None} | "
            f"elapsed={time.perf_counter()-cog_start:.3f}s"
        )

        # 6. Generate Document Report (Phase 3)
        await firestore_service.update_job_status(
            project_id, document_id, "Comparing to existing PDFs", 70
        )
        from datetime import datetime, timezone

        report_start = time.perf_counter()
        logger.info(
            f"[Pipeline] [5/6] Generating markdown report | document={document_id}"
        )
        report_md = report_generator.generate_markdown_report(
            document_name=gcs_path.split("/")[-1],
            upload_timestamp=datetime.now(timezone.utc).isoformat(),
            summary=full_summary,
            cognitive_insights=cognitive_insights,
            similarities=[],
            contradictions=[],
        )
        logger.info(
            f"[Pipeline] [5/6] Report generated | "
            f"report_length={len(report_md)} chars | elapsed={time.perf_counter()-report_start:.3f}s"
        )

        # 6. Embed chunks and upsert into Pinecone vector store, finding Similarities & Contradictions
        vectors_to_upsert = []
        job_similarities = []
        job_contradictions = []
        
        try:
            logger.info(f"[Pipeline] [6/7] Starting Pinecone embeddings & Cross-Document Analysis for document {document_id}")
            from app.vector_store.pinecone_adapter import pinecone_adapter
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            import os
            
            embedding_model = os.environ.get("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
            embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model)
            
            if full_summary:
                sum_vector = await embeddings.aembed_query(full_summary)
                vectors_to_upsert.append({
                    "id": f"{document_id}_summary",
                    "values": sum_vector,
                    "metadata": {
                        "document_id": document_id,
                        "summary": full_summary,
                        "text": full_summary,
                        "type": "summary",
                        "filename": document_name
                    }
                })
                
            if all_claims:
                claim_texts = [c.get("fact", "") for c in all_claims if c.get("fact")]
                if claim_texts:
                    claim_vectors = await embeddings.aembed_documents(claim_texts)
                    
                    from app.agents.contradiction_pipeline.nli_classifier import nli_classifier
                    from app.agents.contradiction_pipeline.verification_pass import verifier_agent
                    
                    active_docs = await firestore_service.get_completed_documents(project_id)
                    active_doc_ids = {doc.get("id") for doc in active_docs if doc.get("id")}
                    
                    async def process_claim(i, claim_text, vector):
                        original_claim = next((c for c in all_claims if c.get("fact") == claim_text), {})
                        source_loc_json = json.dumps(original_claim.get("source_location")) if original_claim.get("source_location") else ""
                        
                        # Query Pinecone for similar vectors
                        matches = await pinecone_adapter.query_vectors(project_id, vector, top_k=3)
                        for match in matches:
                            metadata = match.metadata if hasattr(match, 'metadata') else match.get("metadata", {})
                            score = match.score if hasattr(match, 'score') else match.get("score", 0)
                            match_doc_id = metadata.get("document_id")
                            
                            if match_doc_id == document_id or score < 0.8:
                                continue
                            if match_doc_id not in active_doc_ids:
                                continue
                                
                            match_claim = {
                                "fact": metadata.get("fact"),
                                "source_location": json.loads(metadata.get("source_location", "{}")) if metadata.get("source_location") else {}
                            }
                            
                            try:
                                nli = await nli_classifier.classify_pair(original_claim, match_claim)
                                if nli.relation == "CONTRADICTION":
                                    verified = await verifier_agent.verify_conflict(nli.evidence_a, nli.evidence_b)
                                    if verified.is_contradiction:
                                        job_contradictions.append({
                                            "quote_a": original_claim.get("fact"),
                                            "quote_b": match_claim.get("fact"),
                                            "source_location": original_claim.get("source_location", {}),
                                            "target_source_location": match_claim.get("source_location", {}),
                                            "conflict_type": nli.conflict_type,
                                            "reasoning": verified.reasoning
                                        })
                                elif nli.relation == "ENTAILMENT":
                                    job_similarities.append({
                                        "source_claim": original_claim.get("fact"),
                                        "target_claim": match_claim.get("fact"),
                                        "source_location": original_claim.get("source_location", {}),
                                        "target_source_location": match_claim.get("source_location", {})
                                    })
                            except Exception as e:
                                logger.error(f"[Pipeline] NLI check failed: {e}")
                        
                        vectors_to_upsert.append({
                            "id": f"{document_id}_claim_{i}",
                            "values": vector,
                            "metadata": {
                                "document_id": document_id,
                                "fact": claim_text,
                                "source_location": source_loc_json,
                                "text": claim_text,
                                "type": "claim",
                                "filename": document_name
                            }
                        })
                    
                    sem_nli = asyncio.Semaphore(5)
                    async def process_claim_with_sem(i, claim_text, vector):
                        async with sem_nli:
                            await process_claim(i, claim_text, vector)
                            
                    await asyncio.gather(*(process_claim_with_sem(i, claim_text, vector) for i, (claim_text, vector) in enumerate(zip(claim_texts, claim_vectors))))

            if vectors_to_upsert:
                logger.info(f"[Pipeline] [Upsert] Upserting {len(vectors_to_upsert)} vectors to Pinecone")
                await pinecone_adapter.upsert_vectors(project_id, vectors_to_upsert)
                logger.info("[Pipeline] [Upsert] Pinecone upsert DONE")

        except Exception as e:
            logger.error(f"[Pipeline] [6/7] Failed to embed and upsert to Pinecone: {e}")

        # [7/7] Write final results to Firestore
        logger.info(
            f"[Pipeline] [7/7] Writing final results to Firestore | "
            f"project={project_id} | document={document_id} | "
            f"similarities={len(job_similarities)} | contradictions={len(job_contradictions)}"
        )
        await firestore_service.update_job_status(
            project_id,
            document_id,
            "Completed",
            100,
            "completed",
            document_name=document_name,
            results={
                "summary": full_summary,
                "cognitive_insights": cognitive_insights.model_dump() if hasattr(cognitive_insights, "model_dump") else cognitive_insights,
                "similarities": job_similarities,
                "contradictions": job_contradictions,
                "markdown_report": report_md,
                "claims": [c.model_dump() if hasattr(c, "model_dump") else c for c in all_claims],
            },
        )

        # Trigger Project-Level Synthesis
        logger.info(f"[Pipeline] [Synthesis] Triggering background project synthesis for {project_id}")
        asyncio.create_task(_trigger_project_synthesis(project_id))
    except Exception as e:
        elapsed = time.perf_counter() - pipeline_start
        logger.error(
            f"[Pipeline] ✗ FAILED | project={project_id} | document={document_id} | "
            f"elapsed={elapsed:.3f}s | error_type={type(e).__name__} | error={e}",
            exc_info=True,
        )
        await firestore_service.update_job_status(
            project_id, document_id, "Failed", 0, "failed", document_name=document_name
        )


@router.post("/")
async def handle_pubsub_push(request: Request):
    """
    Endpoint for Google Cloud Pub/Sub Push Subscriptions.
    Receives events when a document is approved and ready for processing.
    Returns 200 immediately so Pub/Sub acks the message;
    actual processing runs as a background task.
    """
    envelope = await request.json()
    if not envelope:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request: empty body"
        )

    message = envelope.get("message")
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request: missing message",
        )

    try:
        data = base64.b64decode(message["data"]).decode("utf-8")
        payload = json.loads(data)

        project_id = payload.get("project_id")
        document_id = payload.get("document_id")
        gcs_path = payload.get("gcs_path")

        if not all([project_id, document_id, gcs_path]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payload missing required fields: project_id, document_id, gcs_path",
            )

        logger.info(
            f"[Worker] Received job for document {document_id} in project {project_id}"
        )

        # Process the document synchronously from the view of the endpoint
        # This prevents the job from being lost if the worker restarts, and 
        # defers the pub/sub ACK until completion.
        await _process_document(project_id, document_id, gcs_path)

        return {"status": "accepted", "document_id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Worker] Error decoding Pub/Sub message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Malformed message: {e}"
        )
