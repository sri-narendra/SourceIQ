# SourceIQ — AI Knowledge Management Platform

Enterprise RAG SaaS — upload documents, chat with them via AI, get answers with source citations. Runs fully locally with a minimal `.env` (no AWS required) and scales to S3/SQS in production.

Stack: Next.js + FastAPI + PostgreSQL/pgvector + AWS (S3/SQS) + Gemini/Groq/OpenAI/Mistral/NVIDIA/OpenRouter/vLLM + OCR (RapidOCR).

**Local-first modes:**
- **Storage**: uses a local-disk fallback (`storage_local/`) when AWS keys are absent
- **Queue**: runs the document pipeline in-process when `SQS_QUEUE_URL` isn't set
- **AI**: uses any configured provider key; drops to a deterministic local fallback if none
- **DB**: auto-provisions the schema (tables + `vector` extension) on startup — no manual SQL required

## Features

- **RAG chat with citations** — retrieve top-k chunks and generate a grounded answer (Groq/Gemini/OpenAI/Mistral/NVIDIA/OpenRouter/vLLM/Ollama) with source scores inline
- **Clickable source previews** — each answer cites the exact source doc; clicking the chip opens a preview: PDFs render in an `<iframe>` that auto-jumps to the cited page via `#page=N`, images render natively, and the retrieved chunk's text shows alongside a **Page N** badge
- **Page-aware retrieval** — PDFs are extracted per page, each chunk tagged with a 1-based `page_number`, so every citation reports which page the answer came from
- **40+ upload formats** — plain text/code, Markdown, CSV, JSON, XML, Office (docx/pptx/xlsx/odt), PDF, and OCR'd images
- **OCR** — scanned PDFs (no text layer) fall back to RapidOCR per page; images (png/jpg/jpeg/bmp/tif/tiff/webp) are OCR'd directly
- **Document status in UI** — sidebar shows per-doc status (`uploading → processing → completed/failed`) and polls while processing
- **Delete anywhere** — workspaces, documents, and chats each have a one-click ✕ delete (doc delete purges the full row graph + S3 object)
- **Reliable async worker** — uploads fire a debounced `workflow_dispatch` (≤1 per 45 s, so bursts coalesce into one run); the one-shot worker keeps polling until the queue is empty, processing up to 4 docs in parallel with per-stage timing logs
- **Multi-file upload** — select several files at once; per-file errors surfaced in the UI
- **Log out** — clears the session token and returns to the login page
- **Neo-brutalist UI** — hard ink borders, offset shadows, halftone paper, marquee ticker (landing), stamped status chips (dashboard)

**Layer responsibilities:**
- `frontend/` — user-facing UI (auth, dashboard, upload, chat)
- `backend/` — REST API, JWT auth, RAG orchestration, DB access
- `workers/` — async document processing pulled from SQS
- `ai/` — chunking, embeddings, vector retrieval, LLM generation
- `storage/` + `queueing/` — S3 file storage and SQS job queue (with local fallbacks)
- `database/` — schema SQL + seed data (Postgres + pgvector)
- `monitoring/` — CloudWatch logging/metrics/alerts
- `shared/` — types/validators shared across modules
- `docker/`, `scripts/`, `docs/` — build config, dev tooling, documentation

## Directory map

```
projectv1/
├── frontend/                 # Next.js + React + TypeScript + Tailwind (see frontend/)
│   ├── src/app/              # pages: / (landing), /login, /dashboard + globals.css
│   ├── src/services/         # axios clients (api.ts + api-endpoints.ts), token in localStorage
│   ├── src/types/            # shared TS interfaces (IChatSource, etc.)
│   ├── e2e/                  # Playwright test (core-flow.spec.ts)
│   └── playwright.config.ts  # starts backend (:8000) + Next (:3100) for E2E
├── backend/                  # FastAPI + SQLAlchemy
│   ├── main.py             # app entry, lifespan (auto schema), CORS, health, routers
│   ├── api/                # auth, workspaces, documents (+ /documents/{id}/preview|file), chat, search, dashboard, users
│   ├── config/settings.py  # pydantic-settings (backend/.env, loaded relative to file)
│   ├── middleware/auth.py  # JWT bearer for protected routes
│   ├── services/, repositories/, models/, schemas/, database/, utils/
│   └── tests/              # pytest + coverage (46 passed, ~70%)
├── ai/                      # framework-agnostic RAG core
│   ├── embeddings/        # providers (Gemini / OpenAI / deterministic local fallback)
│   ├── chunking/          # extract_pages(): per-page text for PDFs, OCR fallback for scans
│   ├── retrieval/         # pgvector search + source formatting (doc, page, score, content)
│   ├── generation/        # per-provider LLM answers (works keyless: deterministic fallback)
│   └── models/            # LLM provider registry (gemini/groq/openai/mistral/nvidia/openrouter/vllm/ollama)
├── workers/                  # background pipeline (SQS-polling)
│   ├── document_worker/    # download → extract → chunk → embed → store (4-thread parallel, debounced dispatch, full-queue drain)
│   ├── embedding_worker/   # re-embed / retry logic
│   ├── notification_worker/
│   └── cleanup_worker/
├── database/                 # migrations/001_init.sql (schema incl. vector ext), seed/001_demo_user.sql
├── storage/s3/client.py      # S3 client + local `storage_local/` fallback
├── queueing/producer.py      # SQS producer (no-op locally when SQS_QUEUE_URL empty)
├── monitoring/               # CloudWatch logging/metrics/alerts scaffold
├── shared/                   # shared constants, types, helpers
├── docker/                   # Dockerfile.backend, Dockerfile.frontend
├── scripts/                  # dev.sh, dev.ps1
├── load/load_test.js         # k6 smoke + ramp load test
├── .github/workflows/ci.yml  # CI: ruff + pytest + frontend build + Playwright E2E
├── docker-compose.yml        # Postgres(pgvector):5433 + backend:8000 + frontend:3000
└── README.md
```

`docs/` contains placeholder dirs (`api/`, `architecture/`, `database/`, `deployment/`) with no files yet — this README is currently the deployment reference.

## Running Locally

### Option A — local Python + Node (needs a Postgres)

The whole app runs with just `DATABASE_URL` — no AWS keys, no Redis, no manual migration. Start a Postgres with pgvector first:

```bash
docker compose up -d db        # Postgres:5433 (repo uses 5433 because 5432 is often taken)
```

Backend (run from repo root — it imports sibling packages `ai/`, `storage/`, `queueing/`):

```powershell
# Windows
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env         # then edit DATABASE_URL + an AI key (optional)
cd ..                          # repo root
python -m uvicorn backend.main:app --app-dir backend --reload   # http://localhost:8000/docs
```

The schema (incl. `vector` extension) is auto-created on boot (`backend/main.py` lifespan). Uploads go to `storage_local/` and process in a background thread; chat answers with citations, and cited sources open previews.

Frontend:

```bash
cd frontend
npm install
npm run dev                    # http://localhost:3000
```

`src/services/api.ts` reads `NEXT_PUBLIC_API_URL` (default `http://localhost:8000/api/v1`).

### Option B — Docker Compose (recommended)

```bash
docker compose up --build
```

Starts Postgres 16 with pgvector (host port **5433**), FastAPI (:8000), and the Next.js frontend (:3000).

> Notes: `backend/.env` is loaded relative to the file, not the CWD — the backend container runs `uvicorn backend.main:app --app-dir backend` from `/app` (repo root inside the container). The frontend container bakes `NEXT_PUBLIC_API_URL` at build time (defaults to `http://localhost:8000/api/v1`); override with `--build-arg NEXT_PUBLIC_API_URL=…` when your API lives elsewhere.

## Deployment

Four production profiles. Everything is optional except `DATABASE_URL` and a way to run the FastAPI app and serve the Next.js build.

### Profile A — single Docker host (simplest, no managed services)

Suitable for a small VPS or a Docker host.

1. Get the code and configure env:

```bash
git clone https://github.com/sri-narendra/SourceIQ.git && cd SourceIQ
cp backend/.env.example backend/.env    # edit DATABASE_URL, JWT_SECRET, add an AI key
cp frontend/.env.local.example frontend/.env.local
```

2. If the frontend will reach the backend at a public URL (different origin from the browser), pass it at build time — it is baked into the static build:

```bash
$env:NEXT_PUBLIC_API_URL="https://api.example.com/api/v1"   # PowerShell
# or: export NEXT_PUBLIC_API_URL=…                         # bash
docker compose up -d --build
```

The compose `ports` map `NEXT_PUBLIC_API_URL` into the frontend image build (`${NEXT_PUBLIC_API_URL:-http://localhost:8000/api/v1}`).

- Frontend: http://server:3000
- Backend API + Swagger: http://server:8000/docs
- Health: `curl http://server:8000/api/v1/health`

> On a single Docker host, `localhost:8000` from the browser usually reaches the backend because compose publishes it; override `NEXT_PUBLIC_API_URL` only when the frontend origin can't use `localhost`.

### Profile B — managed hosts (RECOMMENDED production)

Split: Vercel (Node) for the frontend, Render (Docker) for the backend, Supabase for Postgres + pgvector.

#### B1. Database — Supabase (pgvector included)

1. Create a project; in Database settings copy the **connection string** (use the pooler host, port `6543`).
2. Paste as `DATABASE_URL`:

```
DATABASE_URL=postgresql://postgres.xxxxxxxx:[PASSWORD]@aws-0-<region>.pooler.supabase.com:6543/postgres
```

3. Schema is auto-created on first backend boot, so no manual SQL is required. (Optional: run `database/migrations/001_init.sql` yourself; it is idempotent.)

**Backend — Render:**

1. New **Web Service** → connect your GitHub repo.
2. **Build command**: `docker build -f docker/Dockerfile.backend -t sourceiq-backend .`
3. **Start command** (Render sets `$PORT`; `python -m uvicorn` puts the repo root on `sys.path` so the sibling `backend` package resolves):

```
python -m uvicorn backend.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

4. **Environment** (`Render → Environment`):

```
DATABASE_URL=…                # from Supabase (above)
JWT_SECRET=<random>           # openssl rand -hex 32
SECRET_KEY=<random>           # openssl rand -hex 32
FRONTEND_URL=https://your-app.vercel.app   # CORS allow for your deployed frontend
AI_PROVIDER=gemini            # or groq/openai/mistral/… (leave any *_API_KEY unset to use the deterministic fallback)
GEMINI_API_KEY=…              # (the provider you chose)
REDIS_URL=                    # optional; not required by default

# Optional — enable S3 + SQS at scale:
AWS_REGION=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET_NAME=
SQS_QUEUE_URL=
```

   Host requirement: Render's free/standard plans expose `$PORT`; the Dockerfile default is `8000` if you run it outside Render.

**Backend workers (optional, at scale):** once `SQS_QUEUE_URL` is set, uploads stop processing in-process and are picked up by listeners. Point any container count of the same image at the queue, or deploy `workers/document_worker/main.py` as a background loop (see `queueing/`). Everything else keyed off AWS shared infra.

**Frontend — Vercel:**

1. Import the repo; set **framework preset to Next.js**; **root directory `frontend/`**.
2. Environment variables (only **one** matters):

```
NEXT_PUBLIC_API_URL=https://<backend-url>/api/v1
```

3. Build preset: default Next.js build (static export is not required; `output: "standalone"` is optional declarator). The current image uses standard `next start`.

> The auth is a **JWT in localStorage** (no NextAuth, no Supabase auth, no middleware). So CORS matters: `backend/main.py` allows the origin in `FRONTEND_URL` plus any localhost port. For Vercel you must set `FRONTEND_URL` to the deployed origin or API calls from the browser will be rejected.

**SSR vs static:** `/` is a server component; `/login` and `/dashboard` are `"use client"` with client-side auth. Everything works as a static export or a `next start` server — choose per host. (This repo ships the server variant via Docker.)

### Profile C — fully cloud (AWS-enabled, costs money)

Same as Profile B, plus managed AWS that **incurs charges** (S3 storage, SQS, CloudWatch beyond the free tier, plus possible compute). Choose this when Profile D's free limits — or the managed-host sleep/idle behaviour — no longer fit your load.

1. Create an S3 bucket, an SQS queue, an IAM user with least-privilege (write to the bucket + send/receive on the queue), and a CloudWatch log group. Set the AWS env vars above.
2. Uploads route through S3 via `storage/s3/client.py`; the app falls back to `storage_local/` when unset, so nothing breaks if you skip AWS.
3. Enable workers: a second Render/Fargate container running the same backend image picks jobs off SQS (the producer enqueues only when `SQS_QUEUE_URL` is set).

**CI/CD:** `.github/workflows/ci.yml` already runs on push: ruff + pytest (backend) and eslint + build + Playwright E2E (frontend) against a `pgvector/pgvector:pg16` service. From there it's whatever deploy hook your host exposes (Render/Vercel auto-deploy from push, AWS CodePipeline, etc.).

### Profile D — AWS-included, still free ($0 with the AWS Free Tier)

Want real AWS in the stack (S3 + SQS + CloudWatch) without paying? AWS's **always-free** tiers cover the exact services this app uses, and the only missing piece (Postgres) is hosted free elsewhere because Amazon has no permanently-free PostgreSQL.

**Why this works — what AWS free actually covers:**

| Service | Free allowance | This app uses it for |
|---|---|---|
| S3 | 5 GB storage, 100K GET, 100K PUT / mo | `storage/s3/client.py` (uploads, previews, file downloads) |
| SQS | 1M requests / mo | `queueing/producer.py` — real async pipeline |
| CloudFront | 50 GB egress + 2M HTTP requests / mo | serving previews / presigned URLs at the edge |
| CloudWatch | 10 metrics, 5 GB logs / mo | backend logs via `monitoring/logs/cloudwatch.py` (auto-wired when AWS creds set) |
| IAM (`role`) | free | least-privilege credentials for the backend |

All are **permanently** free (standard per month), not 12-month limited, and **need no starting credits or promo balance** — the always-free tier applies to any AWS account, including one with $0.00 in it. S3/SQS/CloudFront/CloudWatch/Lambda/IAM remain free each month.
**Neon or Supabase** (Free plan) supplies pgvector Postgres — Amazon's only offensive gap (RDS Free Tier is 12-month only).

**The $0 architecture:**

- Frontend: Vercel (free)
- Backend + workers: Render (free tier) or EC2 `t3.micro` Free Tier (12-month promo, if your account has it)
- Database: Neon / Supabase Postgres + pgvector (free)
- Objects → **S3**, jobs → **SQS**, logs/metrics → **CloudWatch**, previews → **CloudFront**

> **On a $0-balance account:** the storage/queue/edge/DB/frontend services above are permanently free and need no credits. Only EC2/RDS "12-month Free Tier" depends on the new-account promo — if your account lacks it, use **Render** (permanent free) for compute and stay with Neon/Supabase for Postgres. That's the default route here.

**Step 1 — Database (Neon or Supabase, free):**

1. Create a project on [neon.tech](https://neon.tech) (or Supabase).
2. Copy the **connection string** (use the pooler host for Neon: `…pooler…`, port 5432).
3. Keep it as we'll set it on the backend below. The schema is auto-created on first boot — no manual SQL.

**Step 2 — AWS account & services (all free tier):**

1. Sign up at https://aws.amazon.com/free (new account → free tier enabled automatically). Open **CloudShell** in the console (top bar) — you'll run everything below from it, no AWS CLI/profiles needed.

2. **S3 bucket** + **SQS queue** — for this repo they were created in the console (S3 → Create bucket `sourceiq-storage`; SQS → Create queue `sourceiq-jobs`, Standard). The equivalent CLI is:

```bash
aws s3 mb s3://sourceiq-storage --region us-east-1                     # create bucket
aws sqs create-queue --queue-name sourceiq-jobs --region us-east-1     # prints the queue URL
# → https://sqs.us-east-1.amazonaws.com/355947669866/sourceiq-jobs
```

3. **(Optional but recommended) CloudFront distribution** pointing at the bucket: Cache origin requests; the app generates presigned URLs so private files stay private even at the edge.

4. **CloudWatch**: nothing to create — with the IAM creds from step 5 set, `backend/main.py` auto-installs `monitoring/logs/cloudwatch.py`, which pushes app logs to the `sourceiq` log group in CloudWatch. It's a no-op without creds.

5. **IAM credentials — user, attached policy, access key** (the exact sequence used for this repo):

   Save the allow policy (least-privilege — exactly S3 bucket + SQS queue + CloudWatch logs) with your real account ID, then create user + key:

   ```bash
cat > sourceiq-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["s3:GetObject","s3:PutObject","s3:DeleteObject","s3:ListBucket"], "Resource": ["arn:aws:s3:::sourceiq-storage","arn:aws:s3:::sourceiq-storage/*"] },
    { "Effect": "Allow", "Action": ["sqs:SendMessage","sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"], "Resource": "arn:aws:sqs:us-east-1:355947669866:sourceiq-jobs" },
    { "Effect": "Allow", "Action": ["logs:PutLogEvents","logs:CreateLogStream","logs:CreateLogGroup"], "Resource": "*" }
  ]
}
EOF

aws iam create-user --user-name sourceiq-backend
aws iam create-policy --policy-name sourceiq-backend --policy-document 'file://sourceiq-policy.json'
# → PolicyArn: arn:aws:iam::355947669866:policy/sourceiq-backend   (copy this)
aws iam attach-user-policy --user-name sourceiq-backend \
    --policy-arn arn:aws:iam::355947669866:policy/sourceiq-backend
aws iam create-access-key --user-name sourceiq-backend
# → prints AccessKeyId + SecretAccessKey — copy BOTH now (secret shows once)
aws iam list-attached-user-policies --user-name sourceiq-backend    # confirm: [ "sourceiq-backend" ]
```

   The `create-access-key` output is the **key instantiation moment** — exactly those two values go into `backend/.env` / Render / EC2. You'll never see the Secret again.

**Step 3 — Backend (Render, free tier; or EC2 t3.micro free tier):**

**Option B2a — Render (free, sleeps when idle):**

1. New **Web Service** → connect your GitHub repo.
2. Build: `docker build -f docker/Dockerfile.backend -t sourceiq-backend .`
3. Start (Render injects `$PORT`):

```
python -m uvicorn backend.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

4. Environment — combine the Profile B list **plus** the AWS vars:

```
DATABASE_URL=postgresql://…#your-neon-or-supabase-url
JWT_SECRET=<openssl rand -hex 32>
SECRET_KEY=<openssl rand -hex 32>
FRONTEND_URL=https://your-app.vercel.app
AI_PROVIDER=gemini
GEMINI_API_KEY=…            # or the provider you chose

# AWS-free-tier variables — the interesting part:
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<from step 2.5 — e.g. AKIA…>
AWS_SECRET_ACCESS_KEY=<from step 2.5>
S3_BUCKET_NAME=sourceiq-storage
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/355947669866/sourceiq-jobs
```

Once these are set, uploads go to **S3** (not `storage_local/`) and document jobs are **enqueued** to SQS instead of running in an inline thread. **The web service no longer processes uploads itself — you must run a worker that consumes the queue:**

```bash
docker run -d --pull always --restart unless-stopped \
  -e DATABASE_URL=… -e AWS_ACCESS_KEY_ID=… -e AWS_SECRET_ACCESS_KEY=… \
  -e S3_BUCKET_NAME=sourceiq-storage -e SQS_QUEUE_URL=… \
  sourceiq-backend python -m workers.document_worker.main
```

(`workers/document_worker/main.py` polls `receive_document_jobs()` in a loop; the same backend image works as this worker; each `--once` pass drains the queue fully with up to 4 threads). Until a worker runs, documents stay stuck in `processing` — that is expected with SQS enabled and by design. On Render+GitHub Actions the backend auto-fires a debounced `workflow_dispatch` per upload (and a `*/5` cron is the safety net), so the managed worker wakes on demand instead of relying only on cron.

**Option B2b — EC2 `t3.micro` (AWS-native compute, 12-month free tier):**

1. Launch an Ubuntu `t3.micro` instance in the free tier.
2. Install Docker; run the same backend image with the AWS env vars:

```
docker run -d --pull always --restart unless-stopped \
  -e DATABASE_URL=… -e JWT_SECRET=… -e SECRET_KEY=… -e FRONTEND_URL=… \
  -e AWS_REGION=us-east-1 -e AWS_ACCESS_KEY_ID=… -e AWS_SECRET_ACCESS_KEY=… \
  -e S3_BUCKET_NAME=sourceiq-storage -e SQS_QUEUE_URL=… \
  -p 80:8000 sourceiq-backend
```

3. Optionally add a **CloudFront** distribution in front of it for HTTP/2 + edge caching. 
(Render is the permanent-free pick; EC2 is the 12-month pick — after year 1 it costs ~$8/mo for the instance.)

**Step 4 — Frontend (Vercel, free):**

1. Import the repo, preset **Next.js**, root **`frontend/`**.
2. Env var (the only one that matters):

```
NEXT_PUBLIC_API_URL=https://my-backend.onrender.com/api/v1
```

3. Deploy. `FRONTEND_URL` on the backend must equal your Vercel origin (CORS).

**Step 5 — verify:**

```
curl -s https://my-backend.onrender.com/api/v1/health
# → {"status":"healthy","database":"connected","storage":"connected","queue":"connected","ai":"available"}
# storage/queue report "connected" only when the AWS vars are all set — that's your signal the S3/SQS paths are live.
```

Then create a workspace, upload a document, and chat. Confirm a doc appears in your S3 bucket list (`s3://sourceiq-storage/docs/…`) to prove the live S3 path. On AWS itself, you can also see the logs landing in CloudWatch → **Log groups → `sourceiq` → `sourceiq-backend`**.

**Step 6 — (optional) make it 100% AWS:**

- **Compute:** swap Render → **Elastic Beanstalk / ECR + ECS Fargate** (free tier for 12 months) — same Dockerfile.
- **DB:** RDS `db.t3.micro` (free tier, 12 months; `CREATE EXTENSION vector` once at boot).
- This keeps everything one-vendor — but you lose *permanent* free on the DB/compute after 12 months. The setup above keeps those two forever-free.

**Cost fallback reminder:** if you exceed any free tier limit (S3 throughput, SQS messages), only *that* overage is billed; the services stay alive. Set an AWS Budget ($1) + alert so you're never surprised.

**Want it to auto-stop at the limit?** AWS Budgets can run a **budget action** that turns the app's AWS access off for you. This repo is already set up this way (`sourceiq-stop` budget + action, account `355947669866`):

1. **Billing → Budgets → Create budget** → amount **$1** (recurring cost).
2. Set a **budget action**: threshold **≥ $1** → **IAM policy action** → **apply the `sourceiq-stop` policy** (a `Deny` on `s3:*`/`sqs:*`/`logs:*`) to the `sourceiq-backend` user. `AUTOMATIC` approval, email subscriber.
3. When actual spend hits $1, AWS attaches the deny policy — an explicit `Deny` **overrides** the step-2.6 allow policy, so the app's S3/SQS/CloudWatch calls fail instantly. Nothing else on your account is touched.

> How to set it up by hand / how this repo's exact setup was created: `aws budgets create-budget --account-id 355947669866 --budget file://budget.json` then `aws budgets create-budget-action --account-id 355947669866 --budget-name sourceiq-stop --action-type APPLY_IAM_POLICY --notification-type ACTUAL --action-threshold ActionThresholdType=ABSOLUTE_VALUE,ActionThresholdValue=1 --definition '{"IamActionDefinition":{"PolicyArn":"arn:aws:iam::355947669866:policy/sourceiq-stop","Users":["sourceiq-backend"]}}' --approval-model AUTOMATIC --subscribers '[{"SubscriptionType":"EMAIL","Address":"you@example.com"}]'` (a `sourceiq-budget-action` IAM role with `iam:AttachUserPolicy` on that user must exist and be trusted by `budgets.amazonaws.com`).

The free tier already keeps everything at $0, so this is a *safety net* in case the limits are exceeded or a key leaks: spend over $1 = the app's AWS access dies, and you're emailed. (Note: S3/SQS are billed per request, so a burst can slightly overshoot $1 before the action fires — the net catches you quickly, not with zero latency.)

### What you must configure in every profile

| Var | Required? | Where |
|---|---|---|
| `DATABASE_URL` | **yes** | all profiles |
| `JWT_SECRET` | **yes** (set a random value in prod) | all profiles |
| `SECRET_KEY` | **yes** (random in prod) | all profiles |
| `AI_PROVIDER` + provider key | no (deterministic fallback otherwise) | B, C |
| `FRONTEND_URL` | yes (CORS) if frontend is not localhost | B, C |
| `NEXT_PUBLIC_API_URL` | yes (frontend build) | all |
| AWS vars | no (local fallbacks) | C, D |

### Verifying a deployment

```bash
curl -s https://api.yourdomain.com/api/v1/health    # {"api":"ok"|"degraded", ...}
```

- `healthy`: DB up; `degraded` just means storage/queue/AI are unconfigured (by design).
- Then hit the frontend: register a user, create a workspace, upload a document, and chat; click the citation chips to open previews.

## Development

```bash
# Windows, one-shot dev runners
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1    # backend only
# or bring-your-own:
python -m uvicorn backend.main:app --app-dir backend --reload
npm --prefix frontend run dev
```

Backend must run **from the repo root** (it imports the sibling `ai/`, `storage/`, `queueing/`, `shared/` packages) — that's why `--app-dir backend` is used.

### Tests

```bash
cd backend
.\.venv\Scripts\python -m pytest -q     # 46 passed, ~70% coverage (needs Postgres on :5433 for integration tests)
.\.venv\Scripts\python -m ruff check .  # clean
```

Unit tests need no DB; integration tests hit real Postgres `ai_knowledge_test` (override with `TEST_DATABASE_URL`). `tests/test_text_extractor.py` covers page-aware extraction (single-page text, per-page PDF via PyMuPDF, unsupported-type errors).

### E2E (Playwright)

```bash
cd frontend
npm run test:e2e    # starts backend:8000 + Next:3100 automatically (playwright.config.ts)
```

Port 3100 is used because 3000 is often taken by a local WSL/Docker service on this machine; CORS allows any localhost port. Install Chromium once: `npx playwright install chromium`.

### Load test (k6, optional)

```bash
k6 run load\load_test.js                # smoke + ramp to 20 VUs
k6 run -e BASE_URL=https://api.yourprod.com/api/v1 load\load_test.js   # against deployed backend
```

Thresholds: p(95) < 1s, error rate < 1%. Uses a pre-registered `load@testmail.dev` (or edit the script).

## API keys (`.env`)

AI provider keys are **optional** — set any of `GROQ_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `NVIDIA_API_KEY`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY` and the generator uses that provider; with no key it returns a deterministic local fallback. Keys live in `backend/.env` (gitignored — never commit it). If you fork and `backend/.env` had real-looking values, rotate them before committing.

## Page-aware pipeline (how citations work)

1. Upload → `document_service` stores bytes (S3 or `storage_local/`) and enqueues (SQS or in-process).
2. `document_worker` (or the in-process path) downloads → `ai/chunking/text_extractor.py:extract_pages()` → per-page splits for PDFs (or RapidOCR per rendered page for scans) → each page chunked & embedded.
3. `ai/retrieval/` searches the vector index; results are formatted by `ai/retrieval/sources.py` — `document_id`, `document`, `page`, `score`, and the chunk `content` itself.
4. The chat UI renders source chips; `dashboard` fetches `GET /documents/{id}/preview` (text) + `GET /documents/{id}/file` (raw bytes, content-type) for the modal (PDF `#page=N`, images, or plain text).