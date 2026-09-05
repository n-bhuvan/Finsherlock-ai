"""RingGuard AI — Stage 21: Analyst Feedback & Governance Telemetry Service.

Provides a lightweight, auditable analyst feedback mechanism:
- Captures feedback categories (explanation useful, insufficient evidence, misleading, outcome confirmed, etc.)
- Records analyst notes with security sanitization and prompt injection scanning
- Links feedback to the cryptographic hash-chained audit trail
- Does NOT alter risk scores, models, calibrations, thresholds, or DB transactions
"""

from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from app.audit.service import HashChainedAuditService
from app.llm.security import SecuritySanitizer


class FeedbackCategory(str, Enum):
    """Categorical classification for human risk analyst feedback."""
    EXPLANATION_USEFUL = "EXPLANATION_USEFUL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    MISLEADING_EXPLANATION = "MISLEADING_EXPLANATION"
    OUTCOME_CONFIRMED = "OUTCOME_CONFIRMED"
    OUTCOME_CONTRADICTED = "OUTCOME_CONTRADICTED"
    GENERAL_ANALYST_NOTE = "GENERAL_ANALYST_NOTE"


class AnalystFeedbackRequest(BaseModel):
    """Payload submitted by a human risk analyst to record feedback on a case."""
    transaction_id: str
    category: FeedbackCategory
    analyst_id: str = "analyst_1"
    notes: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class AnalystFeedbackResponse(BaseModel):
    """Auditable response returned after feedback is recorded."""
    feedback_id: str
    transaction_id: str
    category: FeedbackCategory
    analyst_id: str
    notes: Optional[str] = None
    rating: Optional[int] = None
    timestamp: str
    audit_record_hash: str
    status: str = "RECORDED"
    human_review_required: bool = True
    disclaimer: str = (
        "Analyst feedback is recorded as governance and quality telemetry only. "
        "It does not autonomously modify model weights, risk scores, or database state."
    )


class AnalystFeedbackService:
    """Service to record, query, and audit human analyst case feedback."""

    def __init__(
        self,
        feedback_log_path: Optional[Path] = None,
        audit_service: Optional[HashChainedAuditService] = None,
    ):
        if feedback_log_path:
            self.feedback_log_path = Path(feedback_log_path)
        else:
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parents[2]
            self.feedback_log_path = repo_root / "ml" / "data" / "audit" / "analyst_feedback.jsonl"

        self.feedback_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_service = audit_service or HashChainedAuditService()

    def record_feedback(self, req: AnalystFeedbackRequest) -> AnalystFeedbackResponse:
        """Sanitize and record human analyst feedback into audit chain and persistent log."""
        clean_txn_id = req.transaction_id.strip()
        now_iso = datetime.now(timezone.utc).isoformat()
        feedback_id = f"FB_{uuid4().hex[:12].upper()}"

        # 1. Sanitize notes against script injection and prompt tampering
        clean_notes = None
        if req.notes:
            sanitized = SecuritySanitizer.sanitize_output(req.notes.strip())
            is_injection, _ = SecuritySanitizer.scan_for_prompt_injection(sanitized)
            if is_injection:
                clean_notes = f"[SECURITY_FLAG: INJECTION_PATTERN_DETECTED] {sanitized}"
            else:
                clean_notes = sanitized

        # 2. Append event to HashChainedAuditService
        audit_rec = self.audit_service.append_audit_record(
            audit_id=feedback_id,
            transaction_id=clean_txn_id,
            account_id="N/A",
            provider="ANALYST_PORTAL",
            model_name="HUMAN_ANALYST",
            prompt_version="feedback_v1",
            prompt_sha256="N/A",
            response_sha256="N/A",
            latency_ms=0.0,
            status="FEEDBACK_SUBMITTED",
            grounding_ratio=1.0,
            is_fallback=False,
            security_status="SECURE",
            human_approval_required=True,
        )
        record_hash = audit_rec.get("record_hash", "0" * 64)

        feedback_entry = {
            "feedback_id": feedback_id,
            "transaction_id": clean_txn_id,
            "category": req.category.value,
            "analyst_id": req.analyst_id,
            "notes": clean_notes,
            "rating": req.rating,
            "timestamp": now_iso,
            "audit_record_hash": record_hash,
            "status": "RECORDED",
        }

        # 3. Append to persistent JSONL log
        with open(self.feedback_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_entry) + "\n")

        return AnalystFeedbackResponse(
            feedback_id=feedback_id,
            transaction_id=clean_txn_id,
            category=req.category,
            analyst_id=req.analyst_id,
            notes=clean_notes,
            rating=req.rating,
            timestamp=now_iso,
            audit_record_hash=record_hash,
        )

    def get_feedback(
        self,
        transaction_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[AnalystFeedbackResponse]:
        """Retrieve historical feedback records, optionally filtered by transaction ID."""
        if not self.feedback_log_path.exists():
            return []

        clean_txn_id = transaction_id.strip() if transaction_id else None
        results: List[AnalystFeedbackResponse] = []

        with open(self.feedback_log_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if clean_txn_id and data.get("transaction_id") != clean_txn_id:
                        continue
                    results.append(
                        AnalystFeedbackResponse(
                            feedback_id=data["feedback_id"],
                            transaction_id=data["transaction_id"],
                            category=FeedbackCategory(data["category"]),
                            analyst_id=data["analyst_id"],
                            notes=data.get("notes"),
                            rating=data.get("rating"),
                            timestamp=data["timestamp"],
                            audit_record_hash=data.get("audit_record_hash", "0" * 64),
                        )
                    )
                except Exception:
                    continue

        return results[-limit:][::-1]

    def get_feedback_summary(self) -> Dict[str, Any]:
        """Compute aggregated feedback statistics for governance dashboards."""
        all_fb = self.get_feedback(limit=1000)
        counts: Dict[str, int] = {cat.value: 0 for cat in FeedbackCategory}
        ratings: List[int] = []

        for fb in all_fb:
            cat_val = fb.category.value
            counts[cat_val] = counts.get(cat_val, 0) + 1
            if fb.rating is not None:
                ratings.append(fb.rating)

        mean_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

        return {
            "total_feedback_count": len(all_fb),
            "category_distribution": counts,
            "average_rating": mean_rating,
            "total_rated_count": len(ratings),
            "latest_feedback_timestamp": all_fb[0].timestamp if all_fb else None,
        }
