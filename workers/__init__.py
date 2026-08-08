import sys
from pathlib import Path

# Workers run from the repo root (`python -m workers.document_worker.main`) but share the
# backend's packages (database, models, config, ...), so make backend/ importable too.
_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))