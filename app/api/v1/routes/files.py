from fastapi import APIRouter, Depends, File, Path, UploadFile, status
from sqlalchemy.orm import Session

from app.controllers.file_controller import FileController
from app.controllers.measurement_controller import MeasurementController
from app.db.database import get_db
from app.schemas.file import FileResponse
from app.schemas.measurement import MeasurementsResponse

router = APIRouter()
controller = FileController()
measurement_controller = MeasurementController()


@router.post("/", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return await controller.upload_file(db=db, file=file)


@router.get("/{file_id}", response_model=FileResponse, status_code=status.HTTP_200_OK)
def get_file(
    file_id: int = Path(..., description="ID of the file to retrieve", ge=1),
    db: Session = Depends(get_db),
):
    return controller.get_file(db=db, file_id=file_id)


@router.get(
    "/{file_id}/measurements/",
    response_model=MeasurementsResponse,
    status_code=status.HTTP_200_OK,
)
def get_measurements(
    file_id: int = Path(..., description="ID of the file to fetch measurements for", ge=1),
    db: Session = Depends(get_db),
):
    return measurement_controller.get_measurements(
        db=db,
        file_id=file_id,
    )