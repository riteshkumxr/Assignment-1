from fastapi import APIRouter
from app.api.routes.jobs import router as jobs_router
from app.api.routes.certificates import router as certificates_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(jobs_router)
api_router.include_router(certificates_router)
