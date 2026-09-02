"""SQLAlchemy ORM Model for IP Addresses."""

from typing import List, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class IPAddress(Base):
    """Network IP access point entity associated with transactions."""

    __tablename__ = "ips"

    ip_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    ip_type: Mapped[str] = mapped_column(String(32), nullable=False)
    asn_org: Mapped[str] = mapped_column(String(128), nullable=False)
    country: Mapped[str] = mapped_column(String(8), nullable=False)

    # Relationships
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="ip")

    def __repr__(self) -> str:
        return f"<IPAddress(ip_id='{self.ip_id}', ip='{self.ip_address}', type='{self.ip_type}')>"
