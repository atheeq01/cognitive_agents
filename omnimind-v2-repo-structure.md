# OmniMind v2 — Monorepo Repository Structure

Architectural reference mapping every directory/file to a feature in the OmniMind v2
architecture doc (project-based RBAC, RLS isolation, 5-stage cross-modal contradiction
engine, GCP infra, CI/CD with canary + auto-rollback).

**Layout philosophy:** `apps/` holds the three independently-deployable runtimes (Vite
PWA, FastAPI API, Cloud Run worker). `packages/` holds code shared across runtimes
(generated types, design tokens). `infra/` holds Terraform workspaces (dev/staging/prod)
matching the doc's IaC requirements. `tests/e2e` and `scripts/` sit at root because they
exercise the *whole system*, not a single app.

---

## 0. Key Libraries & Technology Decisions

| Layer | Library / Service | Version | Notes |
|---|---|---|---|
| ORM | **SQLAlchemy** | 2.x (async) | `AsyncSession` + `AsyncEngine`; `DeclarativeBase` for all models |
| Data validation | **Pydantic** | v2 (`BaseModel`) | Request/response DTOs in `schemas/`; also powers UCD & Claim models |
| Vector search | **Pinecone** | `pinecone-client >= 3` | Serverless index, namespace-per-project isolation |
| DB migrations | Alembic | latest | Async-aware `env.py`; vector columns removed — Pinecone manages its own index |
| Web framework | FastAPI | 0.111+ | Async routes; Pydantic v2 native |
| Rate limiting | slowapi | latest | Redis-backed, per-user + per-project |

---

## 1. Top-Level Overview

```
omnimind-v2/
├── .github/
│   └── workflows/                  # GitHub Actions — see Section 6
├── apps/
│   ├── web/                        # React 19 + TS + Vite PWA — Section 2
│   ├── api/                        # FastAPI async backend — Section 3
│   └── worker/                     # Cloud Run event-driven worker — Section 4
├── packages/
│   ├── shared-types/                # cross-app TS contracts generated from pydantic
│   └── ui-tokens/                   # Tailwind/Radix design tokens
├── infra/
│   └── terraform/                   # GCP IaC, dev/staging/prod workspaces — Section 5
├── tests/
│   └── e2e/                         # Playwright, whole-stack isolation/approval flows
├── scripts/                          # ops CLIs (re-embed, seed staging, deletion certs)
├── docs/
│   ├── architecture/                # source-of-truth architecture docs
│   └── runbooks/                    # DLQ alerts, orphaned-admin recovery, etc.
├── docker-compose.yml                # local dev: redis, firestore emu, pinecone-local (postgres runs locally)
├── .env.example                      # non-secret config only — ALL secrets via Secret Manager
├── pnpm-workspace.yaml / turbo.json  # monorepo task graph (web + api + worker)
├── CODEOWNERS                        # enforces "1+ senior engineer" prod approval gate
└── README.md
```

---

## 2. `apps/web/` — React 19 + TypeScript + Vite PWA

```
apps/web/
├── public/
│   ├── manifest.json                 # PWA manifest — installable app
│   └── sw.js                         # service worker — offline upload queue
├── src/
│   ├── main.tsx
│   ├── app/
│   │   ├── App.tsx
│   │   ├── router.tsx                # code-split routes per feature (<150KB initial)
│   │   └── providers/
│   │       ├── AuthProvider.tsx       # Firebase Auth — 15-min JWT, httpOnly refresh cookie
│   │       ├── ProjectProvider.tsx    # holds active_project_id; injects X-Project-ID header
│   │       └── QueryProvider.tsx      # TanStack Query — cache invalidated on project switch
│   │
│   ├── features/
│   │   ├── project-switcher/
│   │   │   ├── ProjectSwitcher.tsx    # header dropdown: name, role badge, member count
│   │   │   ├── CommandPalette.tsx     # Cmd+K — "switch to [project]", jump to conflicts
│   │   │   └── useProjects.ts         # GET /users/me/projects (role per project)
│   │   │
│   │   ├── admin-dashboard/           # Admin-only — not rendered (not just hidden) for non-admins
│   │   │   ├── ApprovalQueue/
│   │   │   │   ├── ApprovalQueueList.tsx   # pending uploads, age indicator, batch-approve
│   │   │   │   └── ApprovalQueueItem.tsx   # approve/reject + optional reason (emailed)
│   │   │   ├── MemberManagement/
│   │   │   │   ├── MemberList.tsx          # invite, role-change, remove, transfer admin
│   │   │   │   └── InviteMemberDialog.tsx
│   │   │   ├── HumanReviewQueue/
│   │   │   │   └── ReviewQueueItem.tsx     # side-by-side evidence — confirm/dismiss/escalate
│   │   │   ├── AuditLog/
│   │   │   │   ├── AuditLogTable.tsx       # filter by user/action/date, CSV export
│   │   │   │   └── useAuditLog.ts
│   │   │   └── CostMetering/
│   │   │       └── UsageDashboard.tsx      # per-project Gemini spend, storage, docs, members
│   │   │
│   │   ├── document-viewer/
│   │   │   ├── SplitPaneViewer.tsx     # PDF.js (left) + extracted insights (right)
│   │   │   ├── PdfViewer.tsx           # lazy page loading — 500pg loads p.1 in <1s
│   │   │   ├── ConflictHighlighter.tsx # red-highlights contradicting spans cross-doc
│   │   │   └── GroundingBadge.tsx      # grounding_confidence vs model_confidence (never one number)
│   │   │
│   │   ├── knowledge-graph/
│   │   │   ├── GraphCanvas.tsx         # Sigma.js WebGL, 10k+ nodes, no frame drops
│   │   │   ├── TemporalEdgeToggle.tsx  # valid_from/valid_to edge display
│   │   │   └── LinkScoreFilter.tsx     # filter ConnectorAgent links by score (0.3–1.0)
│   │   │
│   │   ├── query-chat/
│   │   │   ├── ChatPanel.tsx           # project-scoped semantic query/chat
│   │   │   └── VoiceRecorder.tsx       # MediaRecorder, live transcript + speaker labels
│   │   │
│   │   ├── upload/
│   │   │   ├── ChunkedUploader.tsx     # 5MB chunks, resumable, optimistic "Processing" state
│   │   │   ├── VisibilitySelector.tsx  # project|team|private + privilege_status
│   │   │   └── useJobStatus.ts         # Firestore realtime listener → pipeline stage tracker
│   │   │
│   │   └── settings/
│   │       └── DensityModeToggle.tsx   # compact/normal/reading — persisted to user profile
│   │
│   ├── components/ui/                  # Radix UI + shadcn/ui primitives (Tailwind themed)
│   ├── lib/
│   │   ├── apiClient.ts                # fetch wrapper — attaches JWT + X-Project-ID
│   │   ├── firebase.ts                 # Firebase Auth client init
│   │   └── firestoreListeners.ts       # realtime job status / conflicts subscriptions
│   ├── hooks/
│   └── styles/
│       └── tailwind.config.ts
│
├── vite.config.ts                      # PWA plugin, per-feature code splitting
├── tsconfig.json
└── package.json
```

---

## 3. `apps/api/` — FastAPI Async Backend (Cloud Run, min-instances=1)

```
apps/api/
├── app/
│   ├── main.py                         # app factory — registers all middleware in order
│   │
│   ├── core/
│   │   ├── config.py                   # settings; never loads secrets from env vars
│   │   ├── secrets.py                  # Secret Manager client — Gemini keys, DB creds
│   │   └── logging.py                  # structured JSON logs + trace_id (Cloud Trace)
│   │
│   ├── middleware/
│   │   ├── auth.py                     # Firebase Auth JWT verify — token holds user_id ONLY
│   │   ├── rbac.py                     # require_project_role() — admin>member>viewer check
│   │   ├── rls_context.py              # SET LOCAL app.project_id on the PG session (Layer 2)
│   │   ├── rate_limit.py               # slowapi + Redis — per-user (20/min) & per-project (1k/hr)
│   │   └── query_sanitizer.py          # classifies prompt-injection attempts pre-agent
│   │
│   ├── db/
│   │   ├── session.py                  # SQLAlchemy 2.x AsyncEngine + AsyncSession factory; PgBouncer-fronted pool
│   │   ├── base.py                     # SQLAlchemy DeclarativeBase — all ORM models inherit from here
│   │   └── rls_policies.sql            # ENABLE ROW LEVEL SECURITY + policies, all tables
│   │
│   ├── models/                         # SQLAlchemy 2.x ORM (DeclarativeBase) — mirrors v2 DB schema
│   │   ├── user.py                     # global identity, no project scope
│   │   ├── project.py                  # settings JSONB, upload_approval_required, legal_hold
│   │   ├── project_member.py           # (project_id, user_id) PK, role check constraint
│   │   ├── document.py                 # status, visibility, privilege_status
│   │   ├── claim.py                    # claim metadata + embedding_model_version + speaker_id
   │   │                               #   (embedding vectors stored in Pinecone, not SQL)
│   │   ├── conflict.py                 # severity, conflict_type, evidence trail
│   │   └── audit_log.py                # append-only, INSERT-only, role_at_time
│   │
│   ├── schemas/                        # Pydantic v2 (BaseModel) request/response DTOs
│   │   ├── project.py
│   │   ├── member.py
│   │   ├── document.py
│   │   ├── conflict.py
│   │   └── ucd.py                      # UnifiedCognitiveDocument + Claim pydantic models
│   │
│   ├── routers/
│   │   ├── projects.py                 # create/edit/delete, GET /users/me/projects
│   │   ├── members.py                  # invite/remove/role-change (admin-only)
│   │   ├── documents.py                # upload/list/delete — role + visibility scoped
│   │   ├── approvals.py                # approve/reject pending uploads (admin-only)
│   │   ├── conflicts.py                # conflict list + human review queue
│   │   ├── query.py                    # project-scoped chat / semantic search
│   │   ├── knowledge_graph.py          # entity graph read API
│   │   ├── audit.py                    # read-only audit log + CSV export
│   │   ├── cost_metering.py            # per-project Gemini/storage usage
│   │   └── health.py                   # GET /health — CI/CD smoke test target
│   │
│   ├── services/
│   │   ├── project_service.py          # last-admin-leaves guard, 50-project membership cap
│   │   ├── approval_service.py         # pending → approved → Pub/Sub trigger
│   │   ├── audit_service.py            # write-path for append-only log
│   │   ├── deletion_service.py         # DELETE /projects/{id} — full purge + certificate
│   │   └── cost_metering_service.py    # circuit breaker at 90% daily Gemini budget
│   │
│   ├── agents/                         # Intelligence layer — asyncio.gather fan-out
│   │   ├── orchestrator.py             # per-agent timeouts, partial-result handling
│   │   ├── context_builder.py          # top-k chunks + graph context, project-scoped
│   │   ├── extractor_agent.py          # modality-aware atomic claim extraction
│   │   ├── summarizer_agent.py         # short/long/cross-doc summaries
│   │   ├── connector_agent.py          # scored entity links (exact=1.0 … co-mention=0.3)
│   │   ├── analyst_agent.py            # synthesized insights
│   │   ├── verifier_agent.py           # grounding_confidence vs project UCDs
│   │   │
│   │   ├── contradiction_pipeline/     # ★ the 5-stage cross-modal engine
│   │   │   ├── claim_extractor.py      # Stage 1 — atomic facts + source_span + speaker_id
│   │   │   ├── candidate_selector.py   # Stage 2 — Pinecone query(namespace=project_id, top_k=5, score>0.80)
│   │   │   ├── nli_classifier.py       # Stage 3 — ENTAIL/NEUTRAL/CONTRADICTION + evidence quotes
│   │   │   ├── verification_pass.py    # Stage 4 — fresh-context independent re-check
│   │   │   └── severity_scorer.py      # Stage 5 — CRITICAL/HIGH/LOW → human queue routing
│   │   │
│   │   ├── prompts/
│   │   │   ├── system_prompt_template.py  # "You serve only project {project_id}" boundary
│   │   │   └── output_validator.py        # sliding-window check for leaked system prompt
│   │   │
│   │   └── proactive_loop.py           # Cloud Scheduler entry — idempotent via Cloud Tasks keys
│   │
│   ├── vector_store/
│   │   ├── pinecone_adapter.py         # Pinecone serverless; namespace=project_id isolation (Layer 4)
│   │   │                               #   upsert(vectors, namespace=project_id) / query(namespace=project_id)
│   │   ├── embedding_versioning.py     # tags vectors with embedding_model_version metadata
│   │   └── reembedding_job.py          # per-project re-embed: delete namespace + re-upsert all vectors
│   │   # NOTE: Pinecone serverless is the v2 vector-store source of truth.
│   │   # Each project maps to its own Pinecone namespace — zero cross-project
│   │   # vector leakage enforced at the Pinecone API layer.
│   ├── pubsub/
│   │   ├── publishers.py               # document-uploads, ai-processing, proactive-loop topics
│   │   └── dlq_handler.py              # 5-retry exponential backoff → omnimind-dlq
│   │
│   └── firestore/
│       ├── job_status.py               # projects/{project_id}/jobs/{job_id}
│       ├── conflicts_store.py          # projects/{project_id}/conflicts/{conflict_id}
│       └── graph_edges.py              # temporal edges (valid_from/valid_to/source_doc_id)
│
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── 0001_initial_schema.py
│       ├── 0002_migrate_org_id_to_project_id.py   # ★ the org→project model migration
│       ├── 0003_enable_row_level_security.py      # RLS policies, all tables (Layer 2)
│       ├── 0004_claims_hnsw_index_partitioned.py  # claim-level HNSW, partitioned by project_id
│       ├── 0005_audit_log.py                      # append-only table + role_at_time
│       └── 0006_document_visibility_privilege.py  # visibility + privilege_status fields
│
├── tests/
│   ├── unit/
│   │   ├── test_rbac_role_hierarchy.py
│   │   └── test_severity_scorer.py
│   ├── integration/
│   │   ├── test_cross_project_isolation.py  # ★ required gate before any prod promotion
│   │   ├── test_role_permissions.py         # full role × permission matrix
│   │   ├── test_approval_workflow.py        # upload → pending → approve → AI processes
│   │   ├── test_cross_modal_conflict.py     # voice + PDF known-disagreement pair
│   │   └── test_rate_limits.py              # verifies 429 on 21st req/min
│   └── security/
│       └── test_prompt_injection.py         # known-injection UCD, bandit-adjacent
│
├── Dockerfile                            # multi-stage, amd64+arm64 buildx target
├── pyproject.toml                        # ruff + mypy --strict config
└── requirements.txt
```

---

## 4. `apps/worker/` — Cloud Run Worker (event-driven, min-instances=0)

```
apps/worker/
├── app/
│   ├── main.py                         # Pub/Sub push-subscription entrypoint
│   │
│   ├── ingest/
│   │   ├── router.py                   # dispatches by source_modality (pdf/image/audio/docx)
│   │   └── mime_validator.py           # python-magic on bytes; ZIP-bomb guard (>10x reject)
│   │
│   ├── security/
│   │   ├── clamav_scanner.py           # clamd socket scan → quarantine gs://.../{project_id}/
│   │   └── pdf_sanitizer.py            # pikepdf — strips JS, embedded files, metadata
│   │
│   ├── approval/
│   │   └── gate_check.py               # blocks AI pipeline until status == 'approved'
│   │
│   ├── processors/
│   │   ├── document_ai_processor.py    # Document AI — PDF/DOCX tables, entities, structure
│   │   ├── vision_ocr.py               # Gemini Vision — image + handwriting OCR
│   │   └── speech_to_text.py           # Speech-to-Text V2 + speaker diarization → speaker_id
│   │
│   ├── ucd/
│   │   ├── ucd_builder.py              # normalizes processor output → UnifiedCognitiveDocument
│   │   ├── section_chunker.py          # splits by heading or 512-token fallback
│   │   └── embedder.py                 # chunk-level + claim-level embeddings (versioned)
│   │
│   └── status/
│       └── firestore_writer.py         # writes pipeline stage progress for realtime UI
│
├── tests/
│   ├── test_mime_validator.py
│   └── test_pdf_sanitizer.py
│
├── Dockerfile
└── requirements.txt
```

---

## 5. `infra/terraform/` — GCP IaC (dev / staging / prod workspaces)

```
infra/terraform/
├── modules/
│   ├── networking/                # HTTPS LB + Cloud Armor (OWASP CRS, geo-restrictions) + CDN
│   ├── cloud-run/                  # api (min=1,max=50) + worker (min=0) service definitions
│   ├── cloud-sql/                  # Postgres (SQL data only; vectors live in Pinecone)
│   │                               #   partitioning by project_id
│   ├── firestore/                  # collections: jobs/, conflicts/, graph edges (project-scoped)
│   ├── storage/                    # GCS buckets — IAM Conditions enforce projects/{project_id}/
│   │                               #   path prefix (Layer 3); CMEK config
│   ├── redis/                      # Memorystore — rate-limit counters + embedding cache
│   ├── pubsub/                     # topics + DLQ subscriptions (5-retry) + depth alerting
│   ├── secret-manager/             # Gemini keys, DB creds — zero env-var secrets
│   ├── iam/                        # Workload Identity Federation (no static CI keys)
│   └── monitoring/                 # SLO dashboards, PagerDuty (critical) + Slack (ops) policies
│
└── environments/
    ├── dev/
    │   └── main.tf                  # single-developer sandbox, lowest-cost sizing
    ├── staging/
    │   ├── main.tf                  # omnimind-staging project — synthetic data only
    │   └── seed_synthetic_projects.tf  # seeds projects covering every role/permission combo
    └── prod/
        ├── main.tf
        └── canary.tf                # 10% traffic canary, 5-min window, auto-rollback thresholds
```

---

## 6. `.github/workflows/` — CI/CD Pipeline

```
.github/workflows/
├── pr-checks.yml          # pytest, mypy --strict, ruff, bandit, trivy (dep CVEs),
│                           #   vitest + playwright, cross-project isolation unit tests
├── docker-build.yml        # on merge to main — buildx amd64/arm64, trivy image scan
│                           #   (block on CRITICAL), push gcr.io/.../{api,worker}:{SHA}
├── deploy-staging.yml       # alembic upgrade head (staging) → deploy --no-traffic →
│                           #   smoke test GET /health → 100% traffic → integration suite
├── deploy-production.yml   # manual approval gate (1+ senior eng) → alembic upgrade head
│                           #   (forward-compatible) → 10% canary 5min → auto-rollback or
│                           #   promote to 100% → Slack notify (SHA + revision)
└── security-audit.yml      # scheduled bandit + trivy + dependency review
```

---

## 7. Root-Level Support

```
tests/e2e/
├── playwright.config.ts
├── isolation.spec.ts           # whole-stack cross-project isolation walkthrough
└── approval-flow.spec.ts       # member upload → admin approve → AI processes

scripts/
├── seed_staging.py             # synthetic projects matching role/permission scenarios
├── reembed_project.py          # CLI for per-project re-embedding migration
└── generate_deletion_certificate.py  # GDPR purge cert for DELETE /projects/{id}

docs/
├── architecture/
│   └── omnimind-v2-architecture.md
└── runbooks/
    ├── dlq_depth_alert.md          # operator steps when DLQ depth > 5
    └── orphaned_project_admin.md   # last-admin-leaves → 30-day archive flow
```
