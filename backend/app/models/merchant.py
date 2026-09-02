"""SQLAlchemy ORM Model for Merchants."""

from typing import List, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class Merchant(Base):
    """Commercial merchant entity receiving P2M payment transactions."""

    __tablename__ = "merchants"

    merchant_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    merchant_category: Mapped[str] = mapped_column(String(64), nullable=False)
    merchant_name: Mapped[str] = mapped_column(String(128), nullable=False)
    merchant_risk_rating: Mapped[str] = mapped_column(String(32), nullable=False)

    # Relationships
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="merchant")

    def __repr__(self) -> str:
        return f"<Merchant(merchant_id='{self.merchant_id}', name='{self.merchant_name}', category='{self.merchant_category}')>"
