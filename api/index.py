"""
api/index.py
------------
Vercel Serverless Python entry point exposing the FastAPI `app` ASGI instance.
"""

from backend.main import app

__all__ = ["app"]
