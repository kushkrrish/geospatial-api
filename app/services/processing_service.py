from sqlalchemy.orm import Session

from app.models.file import FileInfo
from app.repositories.feature_repositiory import FeatureRepository
from app.repositories.file_repository import FileRepository
from app.services.geospatial_service import GeospatialService


class ProcessingService:

    def __init__(self):

        self.file_repository = (
            FileRepository()
        )

        self.feature_repository = (
            FeatureRepository()
        )

        self.geospatial_service = (
            GeospatialService()
        )

    def process_file(
        self,
        db: Session,
        file_info: FileInfo
    ):

        self.file_repository.update_processing(
            db=db,
            file_info=file_info,
            status="PROCESSING",
            error_message=None
        )

        try:

            result = (
                self.geospatial_service.process(
                    file_info.file_path
                )
            )

            # Remove previous results.
            # Useful if a file is reprocessed.
            self.feature_repository.delete_by_file_id(
                db=db,
                file_id=file_info.id
            )

            for feature in result["features"]:

                self.feature_repository.create(
                    db=db,
                    file_id=file_info.id,
                    feature_index=feature[
                        "feature_index"
                    ],
                    geometry_type=feature[
                        "geometry_type"
                    ],
                    geometry=feature[
                        "geometry"
                    ],
                    properties=feature[
                        "properties"
                    ],
                    area=feature[
                        "area"
                    ],
                    length=feature[
                        "length"
                    ]
                )

            file_info.status = "COMPLETED"
            file_info.source_crs = (
                result["source_crs"]
            )
            file_info.feature_count = (
                result["feature_count"]
            )
            file_info.error_message = None

            db.commit()
            db.refresh(file_info)

            return file_info

        except Exception as exc:

            db.rollback()

            file_info.status = "FAILED"
            file_info.error_message = str(exc)

            db.commit()

            raise