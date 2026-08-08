# AI Knowledge Management Platform

Enterprise RAG SaaS — upload documents, chat with them via AI, get answers with source citations. Runs fully locally with a minimal `.env` (no AWS required) and scales to S3/SQS in production.

Stack: Next.js + FastAPI + PostgreSQL/pgvector + AWS (S3/SQS) + Gemini/Groq/OpenAI/Mistral/NVIDIA/OpenRouter/vLLM + OCR (RapidOCR).

**Local-first modes:**
- **Storage**: uses a local-disk fallback (`storage_local/`) when AWS keys are absent
- **Queue**: runs the document pipeline in-process when `SQS_QUEUE_URL` isn't set
- **AI**: uses any configured provider key; drops to a deterministic local fallback if none
- **DB**: auto-provisions the schema (tables + `vector` extension) on startup — no manual SQL

## Features

- **RAG chat with citations** — retrieve top-k chunks and generate a grounded answer (Groq/Gemini/OpenAI/Mistral/NVIDIA/OpenRouter/vLLM/Ollama) with source scores inline
- **Clickable source previews** — each answer cites the exact source doc, and clicking the chip opens a preview of the file: PDFs render inline (`<iframe>` auto-jumping to the cited page via `#page=N`), images render natively, and the retrieved chunk's text is shown alongside a **Page N** badge
- **Page-aware retrieval** — PDFs are extracted per page, each chunk is tagged with its 1-based `page_number`, and every source citation reports which page the answer came from
- **40+ upload formats** — plain text/code, Markdown, CSV, JSON, Office (docx/pptx/xlsx/odt), PDF, and OCR'd images
- **OCR** — scanned PDFs fall back to RapidOCR; images (png/jpg/jpeg/bmp/tif/tiff/webp) are OCR'd directly
- **Document status in UI** — sidebar shows per-doc status (`uploading → processing → completed/failed`) and polls while processing
- **Delete anywhere** — workspaces, documents, and chats each have a one-click ✕ delete (no confirmation)
- **Multi-file upload** — select several files at once; per-file errors surfaced in the UI
- **Log out** — dedicated button in the chat header clears the session token and returns to the login page

**Layer responsibilities:**
- `frontend/` — user-facing UI (auth, dashboard, upload, chat)
- `backend/` — REST API, auth, RAG orchestration, DB access
- `workers/` — async document processing pulled from SQS
- `ai/` — chunking, embeddings, vector retrieval, LLM generation
- `storage/` + `queueing/` — AWS S3 file storage and SQS job queue
- `database/` — schema migrations and seed data (Postgres + pgvector)
- `monitoring/` — CloudWatch logging/metrics/alerts
- `shared/` — types/validators shared across modules
- `docker/`, `scripts/`, `docs/` — build config, dev tooling, documentation

## Structure

```
projectv1/
├── frontend/                  # Next.js 16 + React + TypeScript + Tailwind (Vercel)
│   ├── src/app/               # App Router pages & layouts
│   ├── src/components/        # Reusable UI components
│   ├── src/features/          # Feature-specific UI (upload, chat, search, dashboard)
│   ├── src/hooks/             # React hooks (useAuth, useChat, useDocuments)
│   ├── src/lib/               # Third-party client setup (TanStack Query, etc.)
│   ├── src/services/          # API clients (axios + per-resource endpoints)
│   ├── src/types/             # Shared TypeScript interfaces
│   ├── src/constants/         # App constants (file limits, chunk sizes)
│   ├── src/utils/             # Frontend helpers
│   ├── src/styles/            # Global styles / Tailwind config
│   ├── public/                # Static assets
│   ├── tsconfig.json          # create-next-app: strict, @/* alias
│   └── eslint.config.mjs      # create-next-app: ESLint 9 flat config
│
├── backend/                   # FastAPI + SQLAlchemy (Render/Docker)
│   ├── main.py                # App entrypoint, CORS, health check
│   ├── api/                   # HTTP route handlers (auth, chat, documents, search, ...)
│   │                          #   includes GET /documents/{id}/preview + /documents/{id}/file
│   ├── controllers/           # Request/response layer (thin, route-focused)
│   ├── services/              # Business logic (auth, chat, document, search, dashboard)
│   ├── repositories/          # Database access (per-entity repos)
│   ├── models/                # SQLAlchemy entities
│   ├── schemas/               # Pydantic request/response models
│   ├── middleware/            # Auth dependency (JWT bearer)
│   ├── config/                # Settings (pydantic-settings, env-driven)
│   ├── database/              # SQLAlchemy engine + session
│   └── utils/                 # Backend helpers
│
├── workers/                   # Background processing (independent of API)
│   ├── document_worker/       # Download → extract → chunk → embed → store
│   ├── embedding_worker/      # Re-embedding / failed-chunk repair
│   ├── cleanup_worker/        # Expire temp uploads & failed documents (daily)
│   └── notification_worker/   # Async notices (document complete, etc.)
│
├── database/                  # SQL, migrations & seed data
│   ├── migrations/            # Versioned schema migrations
│   ├── seed/                  # Demo/dev seed data
│   ├── functions/             # Postgres functions
│   └── views/                 # Postgres views
│
├── ai/                        # RAG logic (Python, framework-agnostic)
│   ├── embeddings/            # Embedder providers (gemini/openai/local fallback)
│   ├── chunking/              # Text extraction (txt/pdf/docx/pptx/xlsx/odt/image OCR) + chunking
│   │                          #   extract_pages(): per-page text for PDFs, OCR fallback for scans
│   ├── retrieval/             # Vector search + source formatting (doc, page, score, chunk content)
│   ├── generation/            # LLM answer generation per provider
│   ├── prompts/               # Prompt templates
│   └── models/                # LLM provider registry (gemini/groq/openai/mistral/nvidia/openrouter/vllm/ollama)
│
├── storage/                   # Storage client (S3 with local-disk fallback)
│   └── s3/                    # S3 client (upload/download/delete/URLs)
│                             # local fallback: writes storage_local/ when no AWS keys
│
├── queueing/                  # AWS SQS producer/events
│   └── producer.py            # Publish document jobs (no-op locally, in-process fallback)
│
├── monitoring/                # AWS CloudWatch
│   ├── logs/                  # Structured logging setup
│   ├── metrics/               # API/worker metrics
│   └── alerts/                # Alert definitions
│
├── shared/                    # Shared across frontend/backend/workers
│   ├── constants/             # Shared constants
│   ├── types/                 # Shared type definitions
│   ├── validators/            # Shared validation rules
│   └── helpers/               # Common utilities
│
├── docker/                    # Dockerfiles (backend, frontend)
├── scripts/                   # Dev scripts (dev.sh)
├── docs/                      # API, architecture, database, deployment docs
├── .github/workflows/         # CI/CD (GitHub Actions)
├── docker-compose.yml         # Postgres(pgvector) + backend + frontend
├── .gitignore
├── LICENSE
└── README.md
```

## Process

Short-form build steps followed to create this project, plus the files created/edited at each stage.

### 1. Scaffold the repo

```bash
mkdir projectv1 && cd projectv1
git init
```

Created root files: `README.md`, `LICENSE` (MIT), `.gitignore`, `.dockerignore`, `docker-compose.yml`.

### 2. Create module folders

`frontend/`, `backend/`, `workers/`, `database/`, `ai/`, `storage/`, `queueing/`, `monitoring/`, `shared/`, `docker/`, `scripts/`, `docs/`, `.github/workflows/`.

> `queueing/` replaces the spec's `queue/` because a top-level `queue/` package shadows Python's stdlib `queue` and breaks boto3/urllib3.

### 3. Backend — configuration & entry

```bash
cd backend
python -m virtualenv .venv          # if `python -m venv` is unavailable
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Files: `config/settings.py`, `main.py`, `schemas/contracts.py`, `middleware/auth.py`, `database/session.py`, `models/entities.py`.

- `services/auth_service.py` — bcrypt + JWT (swapped out `passlib` — incompatible with bcrypt ≥ 4.1).
- 18 routes across `api/` (auth, workspaces, documents, chat, search, dashboard, users).
- Added `email-validator` (pydantic requires it for `EmailStr`).
- Loosened `langchain-google-genai`/`google-generativeai` pins — the tight pair conflicted on dependency resolution.
- `/` and the backend imports sibling root packages (`ai/`, `storage/`, `queueing/`), so it must run **from the repo root**: `uvicorn backend.main:app --app-dir backend`.

### 4. AI / RAG pipeline

- `ai/embeddings/providers.py` — Gemini/OpenAI + deterministic local fallback.
- `ai/chunking/chunker.py` & `text_extractor.py` — 40+ formats → chunks.
- `ai/retrieval/retriever.py` — cosine search (swap for pgvector HNSW later).
- `ai/generation/generator.py` — per-provider generation (Gemini, Groq, OpenAI-compatible: OpenAI/Mistral/NVIDIA/OpenRouter, plus local vLLM/Ollama), local fallback when no API key.
- `ai/prompts/prompts.py`, `ai/models/registry.py`.

### 4b. Supported document types

40+ formats, driven by `ALLOWED_FILE_TYPES` in `backend/.env` (default in `config/settings.py`):

| Category | Extensions |
|---|---|
| Plain text | `txt md csv tsv json xml html yaml yml rtf log` |
| Code | `py js ts java cpp c h hpp go rs rb php swift kt scala r sh bash sql css scss` |
| Office | `pdf docx pptx xlsx odt` |
| Images (OCR) | `png jpg jpeg bmp tif tiff webp` |

- On upload, storage + background ingest, then chat retrieves from the extracted text.
- **Scanned PDFs** (no text layer, <20 chars extracted) fall back to **RapidOCR** page-by-page (pymupdf render → OCR). Images are always OCR'd.
- **Page-aware extraction** — `ai/chunking/text_extractor.py:extract_pages()` returns per-page text for PDFs, and the `document_worker` chunks each page separately, storing the 1-based `page_number` on every chunk. Formats without a page concept (text/code, Office) are a single page (`page_number = null`).
- Extraction is lazy per type: text/code decode as UTF-8; Office uses python-docx/pptx/openpyxl; PDF uses pypdf (or PyMuPDF for OCR render); ODT via zipfile+xml.

### 5. Storage + queueing

- `storage/s3/client.py` — S3 upload/download/delete/presigned URL, with a local-disk fallback to `storage_local/` when `S3_BUCKET_NAME`/`AWS_ACCESS_KEY_ID` are unset (so uploads work with no AWS).
- `queueing/producer.py` — SQS publish. Without `SQS_QUEUE_URL`, the document pipeline runs in a background thread on upload (`document_service.py:_process_background`), calling the same `workers/document_worker` ingest (extract → chunk → embed → store).

### 6. Workers

- `workers/document_worker/main.py` — download → extract → chunk → embed → store.
- `workers/embedding_worker/`, `workers/cleanup_worker/`, `workers/notification_worker/`.

```bash
python -m workers.document_worker.main
```

### 7. Database

- `database/migrations/001_init.sql` — all 10 tables + pgvector HNSW index.
- `database/seed/001_demo_user.sql` — demo user.

### 8. Frontend — production scaffold with a real command

```bash
npx create-next-app@latest frontend --ts --tailwind --eslint --app --import-alias "@/*" --use-npm
npm install axios
```

The App Router scaffold generates `src/app/`, `tsconfig.json`, Tailwind/ESLint/PostCSS config, and a lint/build toolchain. Our typed files were layered on top under `src/`: `types/index.ts`, `services/api.ts` (axios) + `api-endpoints.ts`, `constants/app.ts`, `utils/helpers.ts`.

Real UI pages live in `src/app/`: `login/page.tsx` (login/register) and `dashboard/page.tsx` (workspaces, document upload, RAG chat, clickable source citations with page-level file previews, doc status + delete, chat delete, log out); `/` redirects to `/login`.

```bash
npm run dev       # http://localhost:3000
npm run build     # verified: static build passes
npx tsc --noEmit  # typecheck clean
```

### 9. Verify

```bash
cd backend
.\.venv\Scripts\python -m pytest -q        # 43 passed, ~77% coverage (needs DB on :5433)
.\.venv\Scripts\python -m ruff check .     # clean
```

Integration tests hit a real Postgres test DB (`ai_knowledge_test` on :5433, set `TEST_DATABASE_URL` to override). Unit tests need no DB. `tests/test_text_extractor.py` covers page-aware extraction (single-page text, per-page PDF via PyMuPDF, unsupported-type errors).

**E2E (Playwright)** — register → login → create workspace → chat:

```bash
cd frontend
npm run test:e2e   # starts backend (:8000) + Next dev (:3100), then drives Chromium
```

`playwright.config.ts` auto-starts both servers (port 3000 is taken by a local Docker/WSL service on this machine, hence 3100); Chromium must be installed once via `npx playwright install chromium`. CORS in `backend/main.py` allows any localhost port, so the E2E frontend origin is accepted.

**Load test** (k6, optional — `choco install k6` or grab a binary from grafana/k6):

```bash
k6 run load\load_test.js              # smoke + ramp to 20 VUs, p95 < 1000ms
k6 run -e BASE_URL=http://host:port load\load_test.js   # against a deployed backend
```

Requires a pre-registered `load@testmail.dev` user (or edit the script to register one first). Thresholds: p95 < 1s, error rate < 1%.

### 10. API keys (`.env`)

AI provider keys are **optional** — set any of `GROQ_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `NVIDIA_API_KEY`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY` and the generator uses that provider; with no key set it returns a deterministic local fallback. Keys for Groq, Mistral, OpenRouter, Gemini, NVIDIA live in `backend/.env`. `backend/.env` is gitignored — never commit it.

### 11. Key settings fixes for local run

- `settings.py` loads `backend/.env` **relative to the file**, not CWD — the backend runs from the repo root.
- Docker DB uses `pgvector/pgvector:pg16` on host port **5433** ([5432 is taken by a local pgvector container]).
- `docker compose down -v` once after a failed first boot to clear a corrupt init volume.
- Schema is auto-provisioned on boot: `backend/main.py` lifespan runs `CREATE EXTENSION IF NOT EXISTS vector` + `Base.metadata.create_all`, so a fresh local DB works with only `DATABASE_URL` set.

---

## Running Locally

### Option A — local (needs only a running Postgres)

The whole app runs with just `DATABASE_URL` — no AWS keys, no Redis, no manual migration. The DB must be reachable (e.g. `docker compose up db` maps Postgres to host port 5433).

```powershell
# Windows (works with a single command):
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
```

Or step by step (run from repo root):

```bash
cd backend
python -m virtualenv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # required: DATABASE_URL (e.g. postgresql://postgres:postgres@localhost:5433/ai_knowledge)
                            # optional: AI provider keys (GROQ_API_KEY, GEMINI_API_KEY, ...)
cd ..                        # run from repo root (sibling packages ai/, storage/, ...)
# NOTE: use `python -m uvicorn`, NOT bare `uvicorn` — the module form adds the
# repo root to sys.path so `import backend.main` resolves.
python -m uvicorn backend.main:app --app-dir backend --reload   # http://localhost:8000/docs
```

On boot the schema is created automatically; uploads write to `storage_local/` and process in a background thread — chat then answers from your documents, and each cited source opens a preview of the exact page the answer came from.

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

### Option B — Docker (recommended)

```bash
docker compose up --build
```

Starts Postgres 16 with pgvector, the FastAPI backend, and the Next.js frontend.

> Notes:
> - DB maps to host port **5433** (5432 is commonly taken by other containers), and `backend/.env` sets `DATABASE_URL=...5433/ai_knowledge`.
> - Use the `pgvector/pgvector:pg16` image (base `postgres:16` lacks the `vector` extension).
> - `backend/config/settings.py` loads `backend/.env` **relative to the file**, so the backend runs correctly from the repo root.
> - Compose config validates; restart Docker Desktop if the daemon isn't running.

---

## Deployment

### Frontend (Vercel)

1. Push the `frontend/` to GitHub.
2. In Vercel, import the repo, set the root to `frontend/`.
3. Add env vars:

```
NEXT_PUBLIC_APP_URL
NEXT_PUBLIC_API_URL
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
NEXTAUTH_SECRET
NEXTAUTH_URL
```

4. Deploy.

### Backend (Render + Docker)

1. In Render create a web service from the repo.
2. Build/start Dockerfile: `docker/Dockerfile.backend` (copies the whole repo — the app imports sibling packages `ai/`, `storage/`, `queueing/`).

```bash
uvicorn backend.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

3. Add env vars:

```
DATABASE_URL
JWT_SECRET
SECRET_KEY
FRONTEND_URL
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
S3_BUCKET_NAME
SQS_QUEUE_URL
GEMINI_API_KEY
GROQ_API_KEY
OPENAI_API_KEY
MISTRAL_API_KEY
NVIDIA_API_KEY
OPENROUTER_API_KEY
REDIS_URL
```

### Database (Supabase)

- Create a Supabase Postgres project (it ships with `pgvector` enabled).
- Set `DATABASE_URL` on the backend.
- Run `database/migrations/001_init.sql` in the SQL editor.

### AWS

Create: S3 Bucket, SQS Queue, IAM user, CloudWatch log group. Add the keys to the backend env vars; set IAM to least-privilege.

### Workers (Render worker service)

Deploy `workers/document_worker/main.py` as a background worker on Render (or run via the same SQS-based container).

### CI/CD

`.github/workflows/` is an (empty) scaffold — add a GitHub Actions workflow (e.g. push → `npm run build` on frontend, `pytest` + `ruff` on backend → deploy) when ready.
