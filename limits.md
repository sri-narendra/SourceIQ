# SourceIQ — Limits, Capacity & Reference Numbers

Verified facts about the deployed SourceIQ platform (frontend on Vercel, backend on Render, Postgres/pgvector on Neon, AWS S3 + SQS, GitHub Actions worker). All numbers are code constants, config values, or measurements taken against the live deployment (UTC, 2026-08-08).

---

## 1 · Project size

| Metric | Value |
| --- | --- |
| Backend source files | **87** `.py` files (excl. `.venv`) |
| Backend lines of code | **2,719** |
| Frontend source files | **13** `.ts` / `.tsx` (excl. `node_modules` / `.next`) |
| Frontend lines of code | **1,021** |
| Python dependencies | **33** pinned in `backend/requirements.txt` |
| REST endpoints | **17** (reads + writes, JWT-guarded) |
| pytest tests | **49** across 13 files |
| Test coverage | **~70%** |
| Playwright E2E suites | 1 (`core-flow.spec.ts`) |
| GitHub Actions workflows | 2 — `ci.yml`, `document-worker.yml` |

## 2 · Stack

| Layer | Technology | Detail |
| --- | --- | --- |
| Web framework | FastAPI | `0.115.0` |
| ASGI server | uvicorn | `0.30.6 [standard]` |
| ORM | SQLAlchemy | `2.0.32` |
| DB driver | psycopg2 | `2.9.9` |
| Vector DB | PostgreSQL + pgvector | `0.3.0`, `vector` ext, PG16 |
| Validation | pydantic | `2.8.2` + settings `2.4.0` |
| Auth | python-jose | `3.3.0`, HS256, JWT bearer |
| Passwords | passlib + bcrypt | `1.7.4` |
| Embeddings | Gemini `text-embedding-004` | pinned 1536 dims; OpenAI fallback `text-embedding-3-small` |
| OCR | RapidOCR (ONNX runtime) | `>=1.3.0` |
| PDF | PyMuPDF + pypdf | `pymupdf>=1.24` |
| Frontend | Next.js App Router + React + TS + Tailwind | — |
| Cloud | S3 + SQS + (opt) CloudFront/CloudWatch | AWS account `355947669866` |
| Hosts | Vercel / Render / Neon | free tiers |

## 3. Feature surface

- RAG chat with **per-page citations**; chat uses `top_k=4`, search endpoint `top_k=5`
- Chunking: **800-word window, 120-word overlap**, 1-based page numbers
- **51** supported file extensions (39 text + 5 binary office + 7 raster images)
- OCR fallback: PDFs whose text layer totals < 20 chars render pages at **200 dpi** and OCR each page
- Status pipeline: `uploading → processing → completed | failed`, polled in UI
- Multi-file upload, delete for workspaces/documents/chats, JWT logout
- Health endpoint `/api/v1/health` reports 4 subsystems

## 4. Endpoints (17 total)

| Router | Routes |
| --- | --- |
| `/auth` | `POST /register`, `POST /login`, `GET /me` |
| `/workspaces` | `POST ""`, `GET ""`, `DELETE /{id}` |
| `/documents` | `POST /upload` (202), `GET ""`, `GET /{id}/preview`, `GET /{id}/file`, `DELETE /{id}` |
| `/chat` | `POST ""`, `GET /history`, `DELETE /{conversation_id}` |
| `/search` | `POST ""` |
| `/dashboard` | `GET ""` |
| `/users` | `PUT /profile` |

## 5. Live deployment (measured)

| Metric | Value |
| --- | --- |
| Registered users | 1 (owner of the `test` workspace) |
| Workspaces | 22 |
| Documents uploaded | 9 (all completed) |
| Conversations | 15 |
| S3 objects | 13 |
| S3 bytes | 1,836,868 B ≈ **1.75 MB** |
| Avg object size | ~ 141 KB |
| Embedding | 1536 dims; ~ 6.3 KB fp32 per vector |

## 6. Limits that bind

### Storage & uploads

| Bound | Value |
| --- | --- |
| Max upload size | **25 MB / file** (`max_file_size_mb = 25`) |
| Supported formats | **51** (`settings.allowed_file_types` = 35 + extractor-only text/code ext) |
| S3 free allowance | 5 GB, 100 K GET + 100 K PUT / month |
| S3 scale ceiling | ≈ 200 K file uploads / month (PUT cap) |
| Current bucket use | 1.75 MB (0.04% of 5 GB) |

### Queue (SQS Standard `sourceiq-jobs`)

| Parameter | Value |
| --- | --- |
| Max batch | 10 messages / poll |
| Worker parallelism | **4 threads** per worker pass |
| Dispatch budget | **1 `workflow_dispatch` per 45 s**, debounced (`document_service.py`) — a burst of uploads coalesces into one run |
| One-shot exhaust | worker `run(once=True)` keeps polling until the batch is empty, so a single dispatch fully drains the queue — no mid-batch waits |
| Visibility timeout | 30 s |
| Message retention | 4 days (345,600 s) |
| Max message size | 1 MB (1,048,576 B) |
| Long-poll wait | 1 s |
| Free allowance | 1 M requests / month |
| Wake-up | instant `workflow_dispatch` per upload (debounced) + `*/5` cron safety |

### Embeddings / inference

| Item | Value |
| --- | --- |
| Embedding dim | 1536 (fixed) |
| Models | Gemini `text-embedding-004` (GPT → 1536), OpenAI fallback |
| Chat context | top_k=4 chunks |
| LLMs | Gemini/Groq/OpenAI/Mistral/NVIDIA/OpenRouter/vLLM/Ollama |
| Retriever | full-table linear cosine, cut to top_k — see scale note |

### Auth & safety

| Item | Value |
| --- | --- |
| JWT | HS256, expiry 1440 min (24 h) |
| Token store | localStorage |
| CORS | any `localhost:*` + `FRONTEND_URL` |
| Rate limiting | none |
| Budget guard | `sourceiq-stop` budget at $1 → IAM deny policy on breach |

## 7. Scale & operational notes

- **Throughput**: load-tested to **20 concurrent VUs**, `p(95) < 1000 ms`, error rate < 1%.
- **Retriever** is O(n) cosine over the workspace's embeddings, cut to `top_k`. Cost grows with chunks per workspace; the code comments flag a pgvector HNSW swap when doc counts grow.
- **Worker**: GitHub Actions runner ~2-core; each pass = fresh checkout (pip cached, `~/.cache/pip` keyed on requirements hash — cache hit ≈ 243 MB) + pip install (~30–45 s cold start) then parallel doc processing. Per-stage timing is logged (download/extract, embed, total) so slow stages show up directly in the run log.
- **Delete** is verified to purge the full row graph: `ProcessingJob` → `Document` → `DocumentChunk` → `Embedding` all cleared (ORM `cascade="all, delete-orphan"`), plus the S3 object. Confirmed with a DB-level delete+count test → 0 rows in every child table afterwards.
- **Render free instance** sleeps after ~50 s idle; first request may add ~50 s cold start.
- **DB scale**: Neon free-tier Postgres is the practical cap (IOV + storage allowance) before billing.
- **Free-tier math for $0**: ~200 K file uploads/mo (S3 PUTS), ~333 K doc jobs/mo (SQS 1 M ÷ 3 msgs), 5 GB storage, 5 GB CloudWatch logs → first-exceeded allowance bills; budget auto-stops AWS access at $1.

## 8. Chunk accounting (from worker logs, sampled)

| Doc | Chunks |
| --- | --- |
| txt smoke / par-a / par-b | 1 each |
| combinational studies.pdf | 2 |
| INT222 / INT252 / PSY291 | 2 each |
| INDUSTRY ETHICS / MVC / others | 1–2 each |

Typical short course PDF → 1–2 chunks; longer docs scale ≈ `⌈words ÷ 800⌉`.

---

_All numbers re-verified at measure time; regenerate by re-running the probes in this doc._