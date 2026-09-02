"""SQLAlchemy ORM Model for Accounts."""

from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.transaction import Transaction


class Account(Base):
    """Account entity linked to customers, transacting across endpoints."""

    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    account_status: Mapped[str] = mapped_column(String(32), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # Scenario Provenance
    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scenario_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ground_truth_label: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="account")

    __table_args__ = (
        Index("ix_accounts_scenario_ground_truth", "scenario_type", "ground_truth_label"),
    )

    def __repr__(self) -> str:
        return f"<Account(account_id='{self.account_id}', scenario='{self.scenario_type}', label='{self.ground_truth_label}')>"
