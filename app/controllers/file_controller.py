from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.services.file_services import FileService


class FileController:

    def __init__(self):
        self.file_service = FileService()
        
    def get_file(self,db: Session,file_id: int):
        return self.file_service.get_file(
            db=db,
            file_id=file_id
        )

    async def upload_file(
        self,
        db: Session,
        file: UploadFile
    ):

        return await self.file_service.upload_file(
            db=db,
            file=file
        )