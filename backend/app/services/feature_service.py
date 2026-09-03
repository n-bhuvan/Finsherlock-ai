"""Feature retrieval service for RingGuard AI.

Stage 8: FastAPI Risk APIs.
Verifies transaction existence in PostgreSQL, enforces point-in-time feature semantics,
and supplies strictly aligned feature vectors for Model A (37 features) and Model B (58 features).
"""

from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import pandas as pd
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class FeatureServiceError(Exception):
    """Base exception for feature service failures."""
    pass


class TransactionNotFoundError(FeatureServiceError):
    """Raised when a requested transaction does not exist in the database."""
    pass


class FeatureStoreError(FeatureServiceError):
    """Raised when feature store files cannot be accessed or parsed."""
    pass


class FeatureService:
    """Service to retrieve point-in-time feature vectors for verified transactions."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parents[2]
            self.data_dir = repo_root / "ml" / "data" / "features"

        self._model_a_df: Optional[pd.DataFrame] = None
        self._model_b_df: Optional[pd.DataFrame] = None
        self._meta_df: Optional[pd.DataFrame] = None

        self._load_feature_store()

    def _load_feature_store(self) -> None:
        """Load and cache the offline point-in-time feature store."""
        path_a = self.data_dir / "model_a_features.csv"
        path_b = self.data_dir / "model_b_features.csv"
        path_meta = self.data_dir / "target_metadata.csv"

        if not path_a.exists():
            raise FeatureStoreError(f"Model A feature store not found at: {path_a}")
        if not path_b.exists():
            raise FeatureStoreError(f"Model B feature store not found at: {path_b}")
        if not path_meta.exists():
            raise FeatureStoreError(f"Target metadata not found at: {path_meta}")

        self._model_a_df = pd.read_csv(path_a, index_col=0)
        self._model_b_df = pd.read_csv(path_b, index_col=0)
        self._meta_df = pd.read_csv(path_meta, index_col=0)

    def verify_transaction_exists(self, db: Session, transaction_id: str) -> Transaction:
        """Verify transaction exists in PostgreSQL database.
        
        Args:
            db: Active SQLAlchemy database session.
            transaction_id: Unique transaction ID string.
            
        Returns:
            Transaction ORM object.
            
        Raises:
            TransactionNotFoundError if record does not exist.
        """
        txn = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if txn is None:
            raise TransactionNotFoundError(f"Transaction '{transaction_id}' not found in database.")
        return txn

    def get_features(
        self,
        db: Session,
        transaction_id: str,
        model_type: str = "graph",
    ) -> Tuple[pd.DataFrame, Transaction]:
        """Retrieve point-in-time feature vector for a transaction.
        
        Args:
            db: Active SQLAlchemy session.
            transaction_id: Transaction identifier.
            model_type: 'baseline' (Model A, 37 features) or 'graph' (Model B, 58 features).
            
        Returns:
            (features_dataframe_single_row, transaction_orm_instance)
        """
        # 1. Database verification
        txn = self.verify_transaction_exists(db, transaction_id)

        # 2. Point-in-time feature vector lookup from verified store
        if model_type == "baseline":
            if self._model_a_df is None or transaction_id not in self._model_a_df.index:
                raise FeatureStoreError(f"Features for transaction '{transaction_id}' not found in Model A store.")
            feat_series = self._model_a_df.loc[[transaction_id]]
            return feat_series, txn

        elif model_type == "graph":
            if self._model_b_df is None or transaction_id not in self._model_b_df.index:
                raise FeatureStoreError(f"Features for transaction '{transaction_id}' not found in Model B store.")
            feat_series = self._model_b_df.loc[[transaction_id]]
            return feat_series, txn

        else:
            raise ValueError(f"Invalid model_type: '{model_type}'. Expected 'baseline' or 'graph'.")


# Global cached singleton instance
_feature_service_instance: Optional[FeatureService] = None


def get_feature_service() -> FeatureService:
    """Retrieve or initialize the global FeatureService singleton."""
    global _feature_service_instance
    if _feature_service_instance is None:
        _feature_service_instance = FeatureService()
    return _feature_service_instance
