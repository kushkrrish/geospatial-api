from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Feature(Base):
    __tablename__ = "features"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    file_id: Mapped[int] = mapped_column(
        ForeignKey("file_info.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    feature_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    geometry_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    geometry: Mapped[Any] = mapped_column(
        Geometry(
            geometry_type="GEOMETRY",
            srid=4326
        ),
        nullable=False
    )

    properties: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )

    area: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    length: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )