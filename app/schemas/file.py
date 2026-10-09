from datetime import datetime

from pydantic import BaseModel


class FileResponse(BaseModel):

    id: int
    filename: str
    status: str
    source_crs: str | None
    feature_count: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }