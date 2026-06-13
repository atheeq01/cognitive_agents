import asyncio
import logging
from typing import Dict, Any

from app.agents.extractor_agent import extractor_agent
from app.agents.summarizer_agent import summarizer_agent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    async def process_chunk(self, project_id: str, chunk_text: str) -> Dict[str, Any]:
        """
        Orchestrates the parallel execution of intelligence agents on a single chunk of text.
        This represents the entry point for the intelligence pipeline.
        """
        logger.info(f"Orchestrator starting parallel processing for project {project_id}")
        
        try:
            # Fan-out: Run Extractor and Summarizer concurrently
            claims_task = asyncio.create_task(
                extractor_agent.extract_claims(project_id, chunk_text)
            )
            summary_task = asyncio.create_task(
                summarizer_agent.summarize_chunk(project_id, chunk_text)
            )
            
            # Wait for both tasks to complete
            claims, summary = await asyncio.gather(claims_task, summary_task)
            
            logger.info(f"Orchestrator completed processing for project {project_id}")
            
            return {
                "summary": summary,
                "claims": [claim.model_dump() for claim in claims]
            }
            
        except Exception as e:
            logger.error(f"Orchestrator failed during processing: {e}")
            raise

orchestrator = AgentOrchestrator()
