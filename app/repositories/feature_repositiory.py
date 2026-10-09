from sqlalchemy import delete
from sqlalchemy.orm import Session
from shapely.geometry import shape as to_shapely_shape
from geoalchemy2.shape import from_shape

from app.models.feature import Feature


class FeatureRepository:

    def delete_by_file_id(
        self,
        db: Session,
        file_id: int
    ):
        db.execute(
            delete(Feature).where(
                Feature.file_id == file_id
            )
        )

    def create(
        self,
        db: Session,
        file_id: int,
        feature_index: int,
        geometry_type: str,
        geometry,
        properties: dict | None,
        area: float | None,
        length: float | None
    ):
        if isinstance(geometry, dict):
            geometry = to_shapely_shape(geometry)  
        feature = Feature(
            file_id=file_id,
            feature_index=feature_index,
            geometry_type=geometry_type,
            geometry=from_shape(
                geometry,
                srid=4326
            ),
            properties=properties,
            area=area,
            length=length
        )

        db.add(feature)

        return feature

    def get_by_file_id(
        self,
        db: Session,
        file_id: int
    ):
        return (
            db.query(Feature)
            .filter(Feature.file_id == file_id)
            .order_by(Feature.feature_index)
            .all()
        )