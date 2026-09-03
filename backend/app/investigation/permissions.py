"""RingGuard AI — Investigation Permission Boundary.

Stage 10: Controlled Investigation Tools.
Enforces explicit authorization for read-only investigation tool operations.
Rejects any mutation or autonomous enforcement flags.
"""

from typing import Set


class PermissionDeniedError(PermissionError):
    """Raised when an unauthorized or mutating operation is requested."""
    pass


class PermissionGuard:
    """Explicit authorization guard for controlled investigation tools."""

    ALLOWED_OPERATIONS: Set[str] = {
        "INVESTIGATION_READ",
        "EVIDENCE_READ",
        "TIMELINE_READ",
        "GRAPH_READ",
    }

    FORBIDDEN_OPERATIONS: Set[str] = {
        "INVESTIGATION_WRITE",
        "DATABASE_WRITE",
        "PAYMENT_ACTION",
        "ACCOUNT_BLOCK",
        "ACCOUNT_UNBLOCK",
        "ENFORCEMENT_ACTION",
        "MODEL_RETRAIN",
    }

    @classmethod
    def check_permission(cls, operation: str = "INVESTIGATION_READ") -> bool:
        """Verify that the requested operation is an authorized read-only action."""
        if operation in cls.FORBIDDEN_OPERATIONS or operation not in cls.ALLOWED_OPERATIONS:
            raise PermissionDeniedError(
                f"Operation '{operation}' is prohibited. Investigation tools are strictly read-only."
            )
        return True
