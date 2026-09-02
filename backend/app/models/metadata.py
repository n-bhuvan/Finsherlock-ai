"""SQLAlchemy ORM Model for Dataset Provenance Metadata."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, BigInteger, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DatasetMetadata(Base):
    """Stores provenance metadata ensuring synthetic origin is strictly documented."""

    __tablename__ = "dataset_metadata"

    metadata_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_name: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(32), nullable=False)
    generator_version: Mapped[str] = mapped_column(String(32), nullable=False)
    random_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entity_counts_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DatasetMetadata(dataset='{self.dataset_name}', seed={self.random_seed}, synthetic={self.synthetic})>"
