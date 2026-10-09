from app.celery_app import celery_app
from app.db.database import SessionLocal
from app.repositories.file_repository import FileRepository
from app.services.processing_service import ProcessingService
from sqlalchemy.exc import OperationalError, DBAPIError
from app.exceptions import PermanentProcessingError


@celery_app.task(
    name="process_geospatial_file",
    bind=True,
    autoretry_for=(OperationalError, DBAPIError, ConnectionError),  # Retry ONLY transient infrastructure bugs
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=3,
)
def process_geospatial_file(self, file_id: int):
    db = SessionLocal()
    file_repository = FileRepository()

    try:
        file_info = file_repository.get_by_id(db, file_id)
        if file_info is None:
            raise PermanentProcessingError(f"File {file_id} not found")

        file_repository.update_status(db, file_id, status="PROCESSING")

        processing_service = ProcessingService()
        processing_service.process_file(db=db, file_info=file_info)

        file_repository.update_status(db, file_id, status="COMPLETED")
        return {"file_id": file_id, "status": "COMPLETED"}

    except (ValueError, PermanentProcessingError) as e:
        # Permanent validation/user error: update DB, DO NOT retry
        db.rollback()
        file_repository.update_status(
            db, file_id, status="FAILED", error_message=str(e)
        )
        return {"file_id": file_id, "status": "FAILED", "error": str(e)}

    except Exception:
        # Unexpected infrastructure errors: rollback & let Celery auto-retry
        db.rollback()
        raise

    finally:
        db.close()