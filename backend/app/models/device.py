"""SQLAlchemy ORM Model for Devices."""

from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class Device(Base):
    """Hardware endpoint entity used by accounts during transactions."""

    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    device_type: Mapped[str] = mapped_column(String(64), nullable=False)
    device_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    device_os: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationships
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="device")

    def __repr__(self) -> str:
        return f"<Device(device_id='{self.device_id}', type='{self.device_type}', os='{self.device_os}')>"
