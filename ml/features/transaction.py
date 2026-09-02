"""RingGuard AI — Point-in-Time Transaction Feature Extractor.

Stage 5: Feature Engineering.
Extracts pure transaction-level features from incoming transaction events.
Uses only fields directly available at transaction time T without looking at the future.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd

TRANSACTION_FEATURE_COLUMNS = [
    "tx_amount",
    "tx_log_amount",
    "tx_hour",
    "tx_day_of_week",
    "tx_day_of_month",
    "tx_is_weekend",
    "tx_is_night",
    "tx_is_transfer_p2p",
    "tx_is_payment_p2m",
    "tx_channel_upi",
    "tx_channel_imps",
    "tx_channel_card",
    "tx_channel_netbanking",
    "tx_has_beneficiary",
    "tx_has_merchant",
]


class TransactionFeatureExtractor:
    """Extracts instantaneous transaction attributes directly observable at execution time."""

    COLUMNS = TRANSACTION_FEATURE_COLUMNS

    @staticmethod
    def extract_features(df_transactions: pd.DataFrame) -> pd.DataFrame:
        """Extract transaction features from transactions DataFrame.
        
        Args:
            df_transactions: DataFrame containing transactions sorted by timestamp.
        
        Returns:
            DataFrame with transaction_id as index and TRANSACTION_FEATURE_COLUMNS.
        """
        df = df_transactions.copy()
        
        # Ensure timestamp is datetime
        ts = pd.to_datetime(df["timestamp"], utc=True)
        amt = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)

        feats = pd.DataFrame(index=df["transaction_id"])
        
        # Monetary features
        feats["tx_amount"] = amt.values
        feats["tx_log_amount"] = np.log1p(np.maximum(0.0, amt.values))

        # Temporal / cyclical features
        feats["tx_hour"] = ts.dt.hour.values
        feats["tx_day_of_week"] = ts.dt.dayofweek.values
        feats["tx_day_of_month"] = ts.dt.day.values
        feats["tx_is_weekend"] = np.isin(feats["tx_day_of_week"], [5, 6]).astype(int)
        feats["tx_is_night"] = np.isin(feats["tx_hour"], [0, 1, 2, 3, 4, 5]).astype(int)

        # Payment type indicators (TRANSFER_P2P, PAYMENT_P2M)
        tx_types = df["transaction_type"].astype(str)
        feats["tx_is_transfer_p2p"] = (tx_types == "TRANSFER_P2P").astype(int).values
        feats["tx_is_payment_p2m"] = (tx_types == "PAYMENT_P2M").astype(int).values

        # Payment channel indicators (UPI, IMPS, CARD, NETBANKING)
        channels = df["channel"].astype(str).str.upper()
        feats["tx_channel_upi"] = (channels == "UPI").astype(int).values
        feats["tx_channel_imps"] = (channels == "IMPS").astype(int).values
        feats["tx_channel_card"] = (channels == "CARD").astype(int).values
        feats["tx_channel_netbanking"] = (channels == "NETBANKING").astype(int).values

        # Endpoint presence indicators
        ben_col = df["beneficiary_id"].fillna("").astype(str).str.strip()
        mer_col = df["merchant_id"].fillna("").astype(str).str.strip()
        feats["tx_has_beneficiary"] = (ben_col != "").astype(int).values
        feats["tx_has_merchant"] = (mer_col != "").astype(int).values

        return feats[TRANSACTION_FEATURE_COLUMNS]
