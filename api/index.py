"""Vercel serverless entry point.

Vercel's Python runtime looks for an ASGI/WSGI `app` in this file. We re-export
the FastAPI app from api.main. The repo root is on sys.path so `engine` imports work.
"""

import sys
from pathlib import Path

# Ensure the repo root is importable (engine/, api/ live there).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.main import app  # noqa: E402

# Vercel's @vercel/python detects `app` (ASGI) automatically.
