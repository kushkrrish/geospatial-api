from fastapi import APIRouter
from app.api.v1.routes.files import router as files_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mounts files.py under /api/v1/files
api_v1_router.include_router(files_router, prefix="/files", tags=["Files v1"])