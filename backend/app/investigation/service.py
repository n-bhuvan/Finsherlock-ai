"""RingGuard AI — Investigation Service Layer.

Stage 10: Controlled Investigation Tools.
Coordinates bounded tool execution, parameter sanitation, and session management.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.investigation.schemas import ToolExecutionResult
from app.investigation import tools


class InvestigationService:
    """Orchestrator for controlled read-only investigation tools."""

    def __init__(self, db: Session):
        self.db = db

    def get_account(self, account_id: str, as_of: Optional[str] = None) -> ToolExecutionResult:
        return tools.get_account(self.db, account_id, as_of=as_of)

    def get_transactions(
        self,
        account_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50,
    ) -> ToolExecutionResult:
        return tools.get_transactions(
            self.db,
            account_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    def find_related_accounts(
        self,
        account_id: str,
        as_of: Optional[str] = None,
        limit: int = 20,
    ) -> ToolExecutionResult:
        return tools.find_related_accounts(self.db, account_id, as_of=as_of, limit=limit)

    def find_shared_devices(self, account_id: str, as_of: Optional[str] = None) -> ToolExecutionResult:
        return tools.find_shared_devices(self.db, account_id, as_of=as_of)

    def find_shared_ips(self, account_id: str, as_of: Optional[str] = None) -> ToolExecutionResult:
        return tools.find_shared_ips(self.db, account_id, as_of=as_of)

    def find_common_beneficiaries(self, account_id: str, as_of: Optional[str] = None) -> ToolExecutionResult:
        return tools.find_common_beneficiaries(self.db, account_id, as_of=as_of)

    def trace_fund_flow(
        self,
        target_id: str,
        as_of: Optional[str] = None,
        max_depth: int = 2,
        max_results: int = 50,
    ) -> ToolExecutionResult:
        return tools.trace_fund_flow(
            self.db,
            target_id,
            as_of=as_of,
            max_depth=max_depth,
            max_results=max_results,
        )

    def reconstruct_timeline(self, target_id: str, as_of: Optional[str] = None) -> ToolExecutionResult:
        return tools.reconstruct_timeline(self.db, target_id, as_of=as_of)

    def get_risk_features(self, transaction_id: str, model_type: str = "graph") -> ToolExecutionResult:
        return tools.get_risk_features(self.db, transaction_id, model_type=model_type)
