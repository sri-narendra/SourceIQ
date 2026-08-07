#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Creating backend venv"
python -m venv backend/venv
source backend/venv/Scripts/activate 2>/dev/null || source backend/venv/bin/activate
pip install -r backend/requirements.txt

echo "==> Starting backend"
uvicorn main:app --reload --port 8000 &

echo "==> Installing frontend deps"
cd frontend
npm install

echo "==> Starting frontend"
npm run dev