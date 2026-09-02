"""SQLAlchemy ORM Model for Transactions."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Numeric, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.device import Device
    from app.models.ip import IPAddress
    from app.models.beneficiary import Beneficiary
    from app.models.merchant import Merchant


class Transaction(Base):
    """Core financial transaction entity preserving exact decimal amounts and scenario provenance."""

    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("accounts.account_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    beneficiary_id: Mapped[Optional[str]] = mapped_column(
        String(32), ForeignKey("beneficiaries.beneficiary_id", ondelete="SET NULL"), nullable=True, index=True
    )
    merchant_id: Mapped[Optional[str]] = mapped_column(
        String(32), ForeignKey("merchants.merchant_id", ondelete="SET NULL"), nullable=True, index=True
    )
    device_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("devices.device_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    ip_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("ips.ip_id", ondelete="RESTRICT"), nullable=False, index=True
    )

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    # Exact numeric type for monetary currency precision (INR)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)

    # Scenario Provenance
    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scenario_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ground_truth_label: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
    device: Mapped["Device"] = relationship("Device", back_populates="transactions")
    ip: Mapped["IPAddress"] = relationship("IPAddress", back_populates="transactions")
    beneficiary: Mapped[Optional["Beneficiary"]] = relationship("Beneficiary", back_populates="transactions")
    merchant: Mapped[Optional["Merchant"]] = relationship("Merchant", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_positive_transaction_amount"),
        Index("ix_transactions_scenario_label", "scenario_type", "ground_truth_label"),
        Index("ix_transactions_account_timestamp", "account_id", "timestamp"),
        Index("ix_transactions_device_timestamp", "device_id", "timestamp"),
        Index("ix_transactions_ip_timestamp", "ip_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id='{self.transaction_id}', acc='{self.account_id}', amt={self.amount}, scenario='{self.scenario_type}')>"
