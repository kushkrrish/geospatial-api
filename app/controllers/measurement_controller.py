from sqlalchemy.orm import Session

from app.services.measurement_service import (
    MeasurementService
)

class MeasurementController:

    def __init__(self):
        self.measurement_service = (
            MeasurementService()
        )

    def get_measurements(
        self,
        db: Session,
        file_id: int
    ):

        return (
            self.measurement_service
            .get_measurements(
                db=db,
                file_id=file_id
            )
        )