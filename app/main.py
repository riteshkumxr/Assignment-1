from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.api.router import api_router
from app.config import settings
from app.dashboard import DASHBOARD_HTML
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and storage on startup
    init_db()
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router)


@app.get("/dashboard", response_class=HTMLResponse, tags=["General"])
def dashboard():
    """Interactive visual web dashboard for bulk certificate generation."""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/", tags=["General"])
def root():
    """Root info endpoint providing API metadata and links."""
    return {
        "title": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "dashboard_url": "/dashboard",
        "endpoints": {
            "dashboard": "GET /dashboard",
            "create_job": "POST /api/v1/jobs",
            "list_jobs": "GET /api/v1/jobs",
            "get_job": "GET /api/v1/jobs/{job_id}",
            "download_zip": "GET /api/v1/jobs/{job_id}/download-zip",
            "get_certificate": "GET /api/v1/certificates/{certificate_id}",
            "download_certificate": "GET /api/v1/certificates/{certificate_id}/download",
        },
    }


@app.get("/health", tags=["General"])
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "storage_writable": settings.storage_path.exists(),
    }
