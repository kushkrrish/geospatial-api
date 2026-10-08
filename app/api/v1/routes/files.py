from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from app.controllers.file_controller import FileController
from app.db.database import get_db
from app.schemas.file import FileResponse

router = APIRouter()
controller = FileController()

@router.post("/", response_model=FileResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await controller.upload_file(db=db, file=file)