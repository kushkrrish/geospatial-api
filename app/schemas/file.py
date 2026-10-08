from datetime import datetime

from pydantic import BaseModel


class FileResponse(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }