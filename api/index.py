"""Vercel Serverless Function entry point for the Clinical Agent API.

This file is automatically detected by Vercel's Python runtime.
It routes requests to the FastAPI application while transparently handling
optional '/api/' path prefixes.
"""

import os
import sys

# Ensure the project root directory is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main import app as clinical_app


class PathRewriterMiddleware:
    """Transparently normalizes paths so both /api/... and direct endpoints work on Vercel."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "")
            if path.startswith("/api/"):
                scope["path"] = path[4:]  # Strip '/api' prefix
            elif path == "/api":
                scope["path"] = "/"
        await self.app(scope, receive, send)


app = PathRewriterMiddleware(clinical_app)
