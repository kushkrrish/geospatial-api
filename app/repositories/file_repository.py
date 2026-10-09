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
            file_path=file_path,
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

    def update_status(
        self,
        db: Session,
        file_id: int,
        status: str,
        error_message: str | None = None
    ) -> Optional[FileInfo]:
        file_info = self.get_by_id(db, file_id)
        if file_info:
            file_info.status = status
            file_info.error_message = error_message
            db.commit()
            db.refresh(file_info)
        return file_info

    def update_processing(
        self,
        db: Session,
        file_info: FileInfo,
        status: str,
        source_crs: str | None = None,
        feature_count: int | None = None,
        error_message: str | None = None
    ) -> FileInfo:

        file_info.status = status

        if source_crs is not None:
            file_info.source_crs = source_crs

        if feature_count is not None:
            file_info.feature_count = feature_count

        file_info.error_message = error_message

        db.commit()
        db.refresh(file_info)

        return file_info