# AI Knowledge Management Platform

Enterprise RAG SaaS — upload documents, chat with them via AI, get answers with source citations.

Stack: Next.js 15 + FastAPI + PostgreSQL/pgvector + AWS (S3/SQS/CloudWatch) + Gemini/Groq/vLLM.

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
├── frontend/                  # Next.js 15 + React + TypeScript + Tailwind (Vercel)
│   ├── app/                   # App Router pages & layouts
│   ├── components/            # Reusable UI components
│   ├── features/              # Feature-specific UI (upload, chat, search, dashboard)
│   ├── hooks/                 # React hooks (useAuth, useChat, useDocuments)
│   ├── lib/                   # Third-party client setup (TanStack Query, etc.)
│   ├── services/              # API clients (axios + per-resource endpoints)
│   ├── types/                 # Shared TypeScript interfaces
│   ├── constants/             # App constants (file limits, chunk sizes)
│   ├── utils/                 # Frontend helpers
│   ├── styles/                # Global styles / Tailwind config
│   └── public/                # Static assets
│
├── backend/                   # FastAPI + SQLAlchemy (Render/Docker)
│   ├── main.py                # App entrypoint, CORS, health check
│   ├── api/                   # HTTP route handlers (auth, chat, documents, search, ...)
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
│   ├── chunking/              # Text extraction + chunking
│   ├── retrieval/             # Vector search + source formatting
│   ├── generation/            # LLM answer generation per provider
│   ├── prompts/               # Prompt templates
│   └── models/                # LLM provider registry (gemini/groq/vllm/ollama)
│
├── storage/                   # AWS S3 utilities
│   ├── s3/                    # S3 client (upload/download/delete/URLs)
│   ├── upload/                # Upload flows
│   └── download/              # Download flows
│
├── queueing/                  # AWS SQS producer/consumer/events
│   │                          # (named 'queueing' to avoid shadowing stdlib 'queue')
│   ├── producer.py            # Publish document jobs
│   ├── consumer/              # SQS consume loop
│   └── events/                # Job event types
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
```

Created root files: `README.md`, `LICENSE` (MIT), `.gitignore`, `docker-compose.yml`.

### 2. Create module folders

`frontend/`, `backend/`, `workers/`, `database/`, `ai/`, `storage/`, `queueing/`, `monitoring/`, `shared/`, `docker/`, `scripts/`, `docs/`, `.github/workflows/`.

> `queueing/` replaces the spec's `queue/` because a top-level `queue/` package shadows Python's stdlib `queue` and breaks boto3/urllib3.

### 3. Backend — configuration & entry

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload   # http://localhost:8000/docs
```

Files: `config/settings.py`, `main.py`, `schemas/contracts.py`, `middleware/auth.py`, `database/session.py`, `models/entities.py`.

- `services/auth_service.py` — bcrypt + JWT (swapped out `passlib` — incompatible with bcrypt ≥ 4.1).
- 18 routes across `api/` (auth, workspaces, documents, chat, search, dashboard, users).

### 4. AI / RAG pipeline

- `ai/embeddings/providers.py` — Gemini/OpenAI + deterministic local fallback.
- `ai/chunking/chunker.py` & `text_extractor.py` — PDF/DOCX/TXT → chunks.
- `ai/retrieval/retriever.py` — cosine search (swap for pgvector HNSW later).
- `ai/generation/generator.py` — per-provider generation, local fallback when no API key.
- `ai/prompts/prompts.py`, `ai/models/registry.py`.

### 5. Storage + queueing

```bash
cd backend
pip install boto3
```

- `storage/s3/client.py` — S3 upload/download/delete/presigned URL.
- `queueing/producer.py`, `queueing/consumer/__init__.py` — SQS publish/consume.

### 6. Workers

- `workers/document_worker/main.py` — download → extract → chunk → embed → store.
- `workers/embedding_worker/`, `workers/cleanup_worker/`, `workers/notification_worker/`.

```bash
python -m workers.document_worker.main
```

### 7. Database

- `database/migrations/001_init.sql` — all 10 tables + pgvector HNSW index.
- `database/seed/001_demo_user.sql` — demo user.

### 8. Frontend

```bash
cd frontend
npm install
npm run dev               # http://localhost:3000
```

- `types/index.ts`, `services/api.ts` (axios) + `services/api-endpoints.ts`.
- `hooks/useAuth.ts`, `hooks/useChat.ts`, `hooks/useDocuments.ts`.
- `app/layout.tsx`, `app/page.tsx`, `constants/app.ts`, `utils/helpers.ts`.

### 9. Verify

```bash
cd backend
python -m py_compile $(find . -name "*.py")
```

Import smoke test confirmed all modules load and the app registers 18 routes.

---

## Running Locally

### Option A — local (needs Postgres)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # set DATABASE_URL, AWS keys
uvicorn main:app --reload
```

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

Starts Postgres 16 (with pgvector), the FastAPI backend, and the Next.js frontend.

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
2. Build/start Dockerfile: `docker/Dockerfile.backend`.

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
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

`.github/workflows/` is scaffolded for GitHub Actions (push → lint, test, deploy).
