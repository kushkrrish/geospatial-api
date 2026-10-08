import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.config.config import settings
from app.repositories.file_repository import FileRepository


class FileService:
    ALLOWED_EXTENSIONS = {".zip", ".kml", ".xml"}

    def __init__(self):
        self.file_repository = FileRepository()

    async def upload_file(
        self,
        db: Session,
        file: UploadFile
    ):
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )

        original_filename = file.filename
        extension = Path(original_filename).suffix.lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {', '.join(sorted(self.ALLOWED_EXTENSIONS))} files are supported"
            )

        unique_filename = f"{uuid.uuid4()}{extension}"

        # Ensure upload directory exists
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

       
        storage_path = upload_dir / unique_filename

        try:
            # Stream write file chunks to disk without size restrictions
            with open(storage_path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):
                    buffer.write(chunk)

            # Save to DB: stores user's original filename and POSIX normalized path
            file_info = self.file_repository.create(
                db=db,
                filename=original_filename,
                file_path=storage_path.as_posix()
            )
            return file_info

        except Exception as err:
            # Cleanup orphaned disk file if stream write or DB transaction fails
            if storage_path.exists():
                storage_path.unlink()

            if isinstance(err, HTTPException):
                raise err
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process file upload: {str(err)}"
            )