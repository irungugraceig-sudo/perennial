"""Vercel serverless entry point.

Vercel passes the full path (e.g. /api/health) to this ASGI app. The real
FastAPI app defines routes without the /api prefix, so we wrap it in an outer
app that mounts it under /api. One mount, no conflicts.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI  # noqa: E402

from api.main import app as _inner  # noqa: E402

app = FastAPI()
app.mount("/api", _inner)
