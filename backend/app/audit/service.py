"""RingGuard AI — Stage 16: Hash-Chained Append-Oriented Audit Log Service.

Implements an append-oriented JSONL audit log with cryptographic SHA-256 hash chaining:
    record_hash = SHA256(previous_record_hash + canonical_record_payload)
First record uses fixed GENESIS_HASH.

Detects record tampering, interior deletion and reordering; external checkpointing is required to detect final-tail deletion/truncation.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

GENESIS_HASH = "0" * 64


class HashChainedAuditService:
    """Append-oriented audit logging with SHA-256 hash chaining."""

    def __init__(self, log_path: Optional[Path] = None):
        if log_path:
            self.log_path = Path(log_path)
        else:
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parents[2]
            self.log_path = repo_root / "ml" / "data" / "audit" / "explanation_audit_log.jsonl"

        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def get_latest_record_hash(self) -> str:
        """Read the last record's hash from the file, or return GENESIS_HASH if empty."""
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return GENESIS_HASH

        last_line = ""
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last_line = line.strip()

        if not last_line:
            return GENESIS_HASH

        try:
            record = json.loads(last_line)
            return record.get("record_hash", GENESIS_HASH)
        except Exception:
            return GENESIS_HASH

    @staticmethod
    def compute_record_hash(previous_record_hash: str, payload: Dict[str, Any]) -> str:
        """Compute SHA-256 hash chaining previous_record_hash with canonical JSON payload."""
        # Canonical JSON serialization with sorted keys
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        chained_input = f"{previous_record_hash}:{canonical_payload}".encode("utf-8")
        return hashlib.sha256(chained_input).hexdigest()

    def append_audit_record(
        self,
        audit_id: str,
        transaction_id: str,
        account_id: str,
        provider: str,
        model_name: str,
        prompt_version: str,
        prompt_sha256: str,
        response_sha256: str,
        latency_ms: float,
        status: str,
        grounding_ratio: float,
        is_fallback: bool,
        fallback_reason: Optional[str] = None,
        security_status: str = "SECURE",
        human_approval_required: bool = True,
    ) -> Dict[str, Any]:
        """Append an auditable record to the hash-chained JSONL log."""
        prev_hash = self.get_latest_record_hash()

        payload = {
            "audit_id": audit_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transaction_id": transaction_id,
            "account_id": account_id,
            "provider": provider,
            "model_name": model_name,
            "prompt_version": prompt_version,
            "prompt_sha256": prompt_sha256,
            "response_sha256": response_sha256,
            "latency_ms": round(latency_ms, 2),
            "status": status,
            "grounding_ratio": round(grounding_ratio, 4),
            "is_fallback": is_fallback,
            "fallback_reason": fallback_reason,
            "security_status": security_status,
            "human_approval_required": human_approval_required,
        }

        record_hash = self.compute_record_hash(prev_hash, payload)

        full_record = {
            "previous_record_hash": prev_hash,
            "record_hash": record_hash,
            **payload,
        }

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(full_record) + "\n")

        return full_record

    def verify_chain_integrity(self) -> Tuple[bool, int, Optional[str]]:
        """Verify the cryptographic hash chain of the entire audit log.
        
        Detects record tampering, interior deletion and reordering;
        external checkpointing is required to detect final-tail deletion/truncation.
        
        Returns:
            (is_valid, record_count, error_message)
        """
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return True, 0, None

        records: List[Dict[str, Any]] = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if line.strip():
                    try:
                        records.append(json.loads(line.strip()))
                    except json.JSONDecodeError as e:
                        return False, len(records), f"Malformed JSON on line {line_no}: {str(e)}"

        if not records:
            return True, 0, None

        expected_prev_hash = GENESIS_HASH

        for idx, rec in enumerate(records):
            actual_prev = rec.get("previous_record_hash")
            actual_rec_hash = rec.get("record_hash")

            if actual_prev != expected_prev_hash:
                return (
                    False,
                    len(records),
                    f"Hash chain broken at index {idx} (audit_id: {rec.get('audit_id')}). "
                    f"Expected previous_record_hash: {expected_prev_hash}, found: {actual_prev}.",
                )

            # Recompute record_hash over payload
            payload = {k: v for k, v in rec.items() if k not in ["previous_record_hash", "record_hash"]}
            computed_hash = self.compute_record_hash(actual_prev, payload)

            if computed_hash != actual_rec_hash:
                return (
                    False,
                    len(records),
                    f"Tampered record payload detected at index {idx} (audit_id: {rec.get('audit_id')}). "
                    f"Computed hash: {computed_hash}, recorded hash: {actual_rec_hash}.",
                )

            expected_prev_hash = actual_rec_hash

        return True, len(records), None

    def get_records(self, limit: int = 50, transaction_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve recent audit records with optional filtering."""
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return []

        all_records: List[Dict[str, Any]] = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line.strip())
                        if transaction_id and rec.get("transaction_id") != transaction_id:
                            continue
                        all_records.append(rec)
                    except Exception:
                        continue

        return list(reversed(all_records))[:limit]
