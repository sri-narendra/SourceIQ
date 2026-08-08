# Deploy & Manage for SourceIQ

This mirrors README Profile D (see `README.md`) but goes deeper on *operating* the deployed app: the exact AWS object names and account used in this repo, key rotation, the $1 stop budget, monitoring, and daily ops.

Reference resources (already provisioned for this project — account `355947669866`, region `us-east-1`):

| What | Name / value |
|---|---|
| S3 bucket | `sourceiq-storage` |
| SQS queue | `sourceiq-jobs` (URL `https://sqs.us-east-1.amazonaws.com/355947669866/sourceiq-jobs`) |
| IAM user | `sourceiq-backend` |
| IAM allow policy | `sourceiq-backend` (attached to the user) |
| IAM deny policy | `sourceiq-stop` (not attached — armed as the budget action) |
| Budget-action role | `sourceiq-budget-action` (trusts `budgets.amazonaws.com`) |
| Budget | `sourceiq-stop`, $1 monthly, starts `2026-08-01` |
| CloudWatch | log group `sourceiq` → stream created lazily by the app |

## Deploy

### 1. Prerequisites

- AWS account (the always-free tier here needs **$0 balance** — no credits).
- A free Neon or Supabase Postgres project (the app needs pgvector; RDS free tier is 12-month only).
- Docker (for the image build / worker).

### 2. Fully-managed (Render + Vercel) — the default

**Backend — Render:**

1. New **Web Service** → connect this repo.
2. Build: `docker build -f docker/Dockerfile.backend -t sourceiq-backend .` (Render builds from `docker/Dockerfile.backend`).
3. Start command (Render injects `$PORT`):

   ```
   python -m uvicorn backend.main:app --app-dir backend --host 0.0.0.0 --port $PORT
   ```

4. Env vars (unset here = on your local `backend/.env` for dev, or in Render for prod):

   ```
   DATABASE_URL=postgresql://<user>:<pass>@<host>/<dbname>?sslmode=require
   JWT_SECRET=<openssl rand -hex 32>
   SECRET_KEY=<openssl rand -hex 32>
   FRONTEND_URL=https://your-app.vercel.app
   AI_PROVIDER=gemini
   GEMINI_API_KEY=...
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=from step "Keys" below
   AWS_SECRET_ACCESS_KEY=from step "Keys" below
   S3_BUCKET_NAME=sourceiq-storage
   SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/AWS_ACCOUNT_ID/sourceiq-jobs
   ```

5. Because the app uses SQS when keys are set, **the web service no longer processes uploads** — it emits jobs to the queue. You **must** run a worker or documents stay in `processing` (by design):

   ```bash
   docker run -d --pull always --restart unless-stopped \
     -e DATABASE_URL=... -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... \
     -e S3_BUCKET_NAME=sourceiq-storage -e SQS_QUEUE_URL=... \
     sourceiq-backend python -m workers.document_worker.main
   ```

**Frontend — Vercel:**

1. Import the repo → preset **Next.js**, root `frontend/`.
2. Env var (the only one): `NEXT_PUBLIC_API_URL=https://<backend>.onrender.com/api/v1`
3. Deploy. `FRONTEND_URL` on the backend must match your Vercel origin for CORS.

### 3. Fully-cloud (AWS alone)

Swap compute/DB for AWS if the 12-month promo applies — same Dockerfile, same env vars:

| Component | Service | Notes |
|---|---|---|
| Compute | EC2 `t3.micro` or ECS Fargate / ECR | same backend image |
| S3 / SQS / CloudWatch | as above | already provisioned |
| DB | RDS `db.t3.micro` | add `CREATE EXTENSION vector` once |

### 4. Local, using real AWS

```bash
docker compose up -d db
cp backend/.env.example backend/.env        # fill real AWS + DB values
scripts/dev.ps1                             # or `python -m uvicorn backend.main:app --app-dir backend --host 0.0.0.0 --port 8000`
```

Then verify: `curl http://localhost:8000/api/v1/health` → `"storage":"connected","queue":"connected"` only when AWS vars are set in `.env`.

## Keys

### Where they live

- Dev: `backend/.env` (git-ignored — never commit).
- Prod: Render/EC2 env vars (never bake into the image).

### Rotation (do this on any suspected leak, or every 90 days)

AWS supports **two** keys per user, so rotating is zero-downtime:

1. In IAM → user `sourceiq-backend` → **Security credentials** → **Create access key** (record the new pair).
2. Put the **new** keys in `backend/.env` (and the Render/EC2 envs). Restart the backend (`--reload` does **not** re-read `.env`; settings load at import).
3. Confirm the app still works (re-run the health check / upload a doc).
4. Back in IAM, **Deactivate** the old key, wait a few days of clean logs, then **Delete** it.
   For a *suspected leak*: deactivate immediately, then delete when you've seen clean logs (never keep 2 active keys long-term).

### Least-privilege check

The allow policy (`sourceiq-backend`, created in README Step 2.5) lets it only S3 bucket `sourceiq-storage`, SQS queue `sourceiq-jobs`, and CloudWatch logs. If you run `aws s3 ls` with these keys, `ListAllMyBuckets` is denied — that's correct (least-privilege, not broken).

## Cost control: the $1 stop

Already armed in this account, but here's the mechanics + how to re-create or adjust:

1. Policy `sourceiq-stop` — an **explicit Deny** on `s3:*`, `sqs:*`, `logs:*`:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       { "Effect": "Deny", "Action": ["s3:*", "sqs:*", "logs:*"], "Resource": "*" },
       { "Sid": "AllowCloudWatch", "Effect": "Allow", "Action": "cloudwatch:*", "Resource": "*" }
     ]
   }
   ```
2. A **budget** of **$1/month** (recurring cost; the always-free tier makes spend normally $0, so hitting $1 = leakage/anomaly).
3. A **budget action**: at threshold $1 → budget role `sourceiq-budget-action` (trusts `budgets.amazonaws.com`) attaches `sourceiq-stop` to user `sourceiq-backend`.

On `$1` spend, the Deny policy attaches, overriding the allow policy — the app's AWS calls instantly fail (uploads + queue), and you're emailed. CloudWatch log emits 401 ~ access-denied on attach. Nothing *else* you ever build is touched (Deny is scoped to S3/SQS/log-groups only, per the JSON above).

### Manage the budget action

- **See it:** Billing → Budgets → `sourceiq-stop`; or `aws budgets describe-budget-action --account-id 355947669866 --budget-name sourceiq-stop --action-id <id> --region us-east-1`.
- **Pause it:** temporarily raise the action's `ActionThresholdValue` to e.g. `10` so it won't fire, then lower it back after. (There is no AWS "disable action" toggle, so threshold-raise is the lazy, reversible pause.)
- **Un-stop after it fired:** `aws iam detach-user-policy --user-name sourceiq-backend --policy-arn arn:aws:iam::355947669866:policy/sourceiq-stop`, and confirm with `aws iam list-attached-user-policies --user-name sourceiq-backend`.

CLI creation recipe (exactly what this repo used):

```bash
# 1. allow-policy JSON per README Step 2.5 → file allow.json
# 2. user + policy + key
aws iam create-user --user-name sourceiq-backend
aws iam create-policy --policy-name sourceiq-backend --policy-document 'file://allow.json'
# → PolicyArn: arn:aws:iam::355947669866:policy/sourceiq-backend
aws iam attach-user-policy --user-name sourceiq-backend --policy-arn arn:aws:iam::355947669866:policy/sourceiq-backend
aws iam create-access-key --user-name sourceiq-backend                # prints AccessKeyId/Secret once
# 3. storage + queue
aws s3 mb s3://sourceiq-storage --region us-east-1
aws sqs create-queue --queue-name sourceiq-jobs --region us-east-1
# 4. budget-role that lets Budgets attach/detach the deny policy
aws iam create-role --role-name sourceiq-budget-action --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"budgets.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws iam put-role-policy --role-name sourceiq-budget-action --policy-name sourceiq-budget-perm --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["iam:AttachUserPolicy","iam:DetachUserPolicy","iam:GetPolicy"],"Resource":"*"}]}'
# 5. budget + stop action (deny-policy JSON is in the section above → file `deny.json` → managed/attached as arn:…:policy/sourceiq-stop)
aws budgets create-budget --account-id 355947669866 --region us-east-1 --budget '{"BudgetName":"sourceiq-stop","BudgetLimit":{"Amount":"1","Unit":"USD"},"BudgetType":"COST","TimeUnit":"MONTHLY","TimePeriod":{"Start":"2026-08-01T00:00:00Z","Inclusive":true}}'
aws budgets create-budget-action --account-id 355947669866 --budget-name sourceiq-stop \
  --action-type APPLY_IAM_POLICY --notification-type ACTUAL \
  --execution-role-arn arn:aws:iam::355947669866:role/sourceiq-budget-action \
  --action-threshold '{"ActionThresholdType":"ABSOLUTE_VALUE","ActionThresholdValue":1}' \
  --definition '{"IamActionDefinition":{"PolicyArn":"arn:aws:iam::355947669866:policy/sourceiq-stop","Users":["sourceiq-backend"]}}' \
  --approval-model AUTOMATIC --subscribers '[{"SubscriptionType":"EMAIL","Address":"you@example.com"}]' --region us-east-1
```

## Day-to-day ops

### Who does what

- Upload lands → `sourceiq-storage/docs/` (S3); a document record is created.
- A job is pushed → `sourceiq-jobs` (SQS) waits for the worker.
- Worker `python -m workers.document_worker.main` polls `receive_document_jobs()` and processes embeddings.
- Logs stream to CloudWatch (`sourceiq` → `sourceiq-backend`) when keys are set.

### Daily checks

| Thing | Where | Healthy when |
|---|---|---|
| App | `GET /api/v1/health` | `status: healthy`, `db/storage/queue: connected` |
| Queue depth | `aws sqs get-queue-attributes --queue-url <url> --region us-east-1 --attribute-names ApproximateNumberOfMessages` | low; if high → workers offline |
| Cost | Billing → Budgets | at/near $0 (usual); watch $1 alert |
| Logs | CloudWatch → Log groups → `sourceiq` | recent events, no repeated access-denied |

### Logs & metrics basics

- CloudWatch auto-wired (group `sourceiq`). To stop logging, unset `AWS_ACCESS_KEY_ID`.
- No app throws fatally on AWS errors (fail happens only when keys set); a `storage: not_configured` health = keys missing.

## Common failure tables

| Symptom | Cause | Fix |
|---|---|---|
| `/health` says `storage/queue not_configured`, uploads saved to `storage_local/` | keys absent in `.env` | add AWS vars + restart backend |
| Uploads say `processing` forever | no worker running | run the worker (queue form), or drop SQS for dev |
| `AccessDenied` after creating bucket/key | attached policy restricted | the exact allow policy JSON in README 6 |
| `ListAllMyBuckets` denied | least privilege by design | not a bug — use `s3 ls s3://sourceiq-storage` instead |

## Key scoping / security

- IAM policy allows only `arn:aws:s3:::sourceiq-storage` — no cross-bucket touch.
- Keys are used only server-side. CORS on the backend only lets your frontend origin talk to it.
- Rotate keys whenever a developer leaves, or a secret shows in the pastebin, or every ~90 days.

## Terms

- `$0`: always-free tier (S3 5GB, 1M*SQS, CloudWatch 5GB) has **no** promo cut-off — recurring monthly.
- On Render: app has a web process + a worker process. Render free also spins down when idle.
- If you exceed a free limit, only *overage* is billed; the services keep running (budget kills the app at $1 to avoid surprises).