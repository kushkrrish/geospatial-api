from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.feature_repositiory import FeatureRepository
from app.repositories.file_repository import FileRepository


class MeasurementService:

    def __init__(self):

        self.file_repository = (
            FileRepository()
        )

        self.feature_repository = (
            FeatureRepository()
        )

    def get_measurements(
        self,
        db: Session,
        file_id: int
    ):

        file_info = (
            self.file_repository.get_by_id(
                db,
                file_id
            )
        )

        if file_info is None:

            raise HTTPException(
                status_code=404,
                detail="File not found"
            )

        if file_info.status == "FAILED":

            raise HTTPException(
                status_code=422,
                detail={
                    "message": "File processing failed",
                    "error": file_info.error_message
                }
            )

        features = (
            self.feature_repository.get_by_file_id(
                db,
                file_id
            )
        )

        measurements = []

        for feature in features:

            measurements.append({
                "feature_id": feature.id,

                "feature_index": (
                    feature.feature_index
                ),

                "geometry_type": (
                    feature.geometry_type
                ),

                "area": feature.area,

                "area_unit": (
                    "m²"
                    if feature.area is not None
                    else None
                ),

                "length": feature.length,

                "length_unit": (
                    "m"
                    if feature.length is not None
                    else None
                ),

                "properties": feature.properties
            })

        return {
            "file_id": file_id,
            "status": file_info.status,
            "feature_count": (
                file_info.feature_count or 0
            ),
            "measurements": measurements
        }