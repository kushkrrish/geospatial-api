from typing import Optional
from sqlalchemy.orm import Session
from app.models.file import FileInfo


class FileRepository:

    def create(
        self,
        db: Session,
        filename: str,
        file_path: str
    ) -> FileInfo:
        file_info = FileInfo(
            filename=filename,   
            file_path=file_path, # Physical disk path (e.g., "storage/uploads/a3b1...kml")
            status="PENDING"
        )
        db.add(file_info)
        db.commit()
        db.refresh(file_info)
        return file_info

    def get_by_id(
        self,
        db: Session,
        file_id: int
    ) -> Optional[FileInfo]:
        return db.query(FileInfo).filter(FileInfo.id == file_id).first()