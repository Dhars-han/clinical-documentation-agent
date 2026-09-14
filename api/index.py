"""Vercel Serverless Function entry point for the Clinical Agent API.

This file is automatically detected by Vercel's Python runtime.
It exports the native FastAPI ASGI app instance.
"""

import os
import sys
import traceback
import logging

# Ensure both project root and api directory are on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

for p in [PROJECT_ROOT, CURRENT_DIR, os.getcwd()]:
    if p and p not in sys.path:
        sys.path.insert(0, p)

try:
    from fastapi import Request
    from backend.main import app

    @app.middleware("http")
    async def rewrite_api_prefix(request: Request, call_next):
        """Transparently strips '/api' prefix so both /api/... and direct endpoints work on Vercel."""
        if request.scope.get("path", "").startswith("/api/"):
            request.scope["path"] = request.scope["path"][4:]
        elif request.scope.get("path", "") == "/api":
            request.scope["path"] = "/"
        response = await call_next(request)
        return response

except Exception as err:
    logging.error(f"CRITICAL: Failed to load FastAPI app on Vercel: {err}\n{traceback.format_exc()}")
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI()

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    def fallback_diagnostics(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Serverless Function Initialization Error",
                "detail": str(err),
                "sys_path": sys.path[:5],
                "cwd": os.getcwd(),
                "traceback": traceback.format_exc().split("\n")
            }
        )
