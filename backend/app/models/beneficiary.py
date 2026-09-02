"""SQLAlchemy ORM Model for Beneficiaries."""

from typing import List, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class Beneficiary(Base):
    """Beneficiary recipient entity for P2P/outbound fund transfers."""

    __tablename__ = "beneficiaries"

    beneficiary_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    beneficiary_type: Mapped[str] = mapped_column(String(64), nullable=False)
    bank_ifsc_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    account_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationships
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="beneficiary")

    def __repr__(self) -> str:
        return f"<Beneficiary(beneficiary_id='{self.beneficiary_id}', type='{self.beneficiary_type}', ifsc='{self.bank_ifsc_prefix}')>"
