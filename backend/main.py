"""
backend/main.py
---------------
Main FastAPI application entry point.
Initializes database tables, seeds default administrator, mounts API routers,
and serves responsive frontend static assets.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_NAME,
    FRONTEND_DIR,
    BASE_DIR
)
from backend.database import Base, engine, SessionLocal
from backend.models import User
from backend.security import hash_password

from backend.routers.auth import router as auth_router
from backend.routers.admin import router as admin_router
from backend.routers.excel import router as excel_router
from backend.routers.generator import router as generator_router


def seed_administrator():
    """
    Ensures a master administrator account exists on platform boot.
    """
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == DEFAULT_ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                email=DEFAULT_ADMIN_EMAIL,
                full_name=DEFAULT_ADMIN_NAME,
                hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print(f"[BOOTSTRAP] Master Admin initialized: {DEFAULT_ADMIN_EMAIL}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create all tables & seed admin
    Base.metadata.create_all(bind=engine)
    seed_administrator()
    yield
    # Shutdown logic (if any)


app = FastAPI(
    title="Patel'Spark - Automation Slide Generator",
    description="Automated platform converting Excel workbooks into executive PowerPoint presentations.",
    version="1.0.0",
    lifespan=lifespan
)

# Ensure database tables and master administrator exist even in serverless environments
try:
    Base.metadata.create_all(bind=engine)
    seed_administrator()
except Exception:
    pass


# Enable CORS for local and networked clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_cache_headers_middleware(request: Request, call_next):
    """
    Injects enterprise HTTP security headers (OWASP best practices) and prevents
    stale browser caching of frontend JS/CSS/HTML assets.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    path = request.url.path
    if path == "/" or path.endswith((".js", ".css", ".html")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Mount API Routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(excel_router)
app.include_router(generator_router)

# Health Check
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Patel'Spark Automation Slide Generator", "version": "1.0.0"}

# Mount Frontend static files
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
    
    sample_dir = BASE_DIR / "sample_ups_data"
    if sample_dir.exists():
        app.mount("/sample_ups_data", StaticFiles(directory=sample_dir), name="sample_ups_data")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa_fallback(full_path: str):
        # Serve index.html for frontend navigation if not an API path
        file_path = FRONTEND_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIR / "index.html")
