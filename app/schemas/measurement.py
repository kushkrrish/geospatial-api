from pydantic import BaseModel


class MeasurementResponse(BaseModel):

    feature_id: int
    feature_index: int
    geometry_type: str

    area: float | None
    area_unit: str | None

    length: float | None
    length_unit: str | None
    properties: dict | None
    
class MeasurementsResponse(BaseModel):

    file_id: int
    status: str
    feature_count: int
    measurements: list[MeasurementResponse]