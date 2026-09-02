"""RingGuard AI — Point-in-Time Behavioral Feature Extractor.

Stage 5: Feature Engineering.
Computes point-in-time historical and velocity features for each transaction.
CRITICAL INVARIANT: For a transaction at time T, all features use strictly prior
transactions where t < T. Future transactions (t > T) have zero influence.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Tuple
import numpy as np
import pandas as pd

BEHAVIORAL_FEATURE_COLUMNS = [
    "beh_account_age_days",
    "beh_tx_sequence_num",
    "beh_time_since_last_tx_sec",
    "beh_is_first_tx",
    "beh_hist_tx_count",
    "beh_hist_total_amount",
    "beh_hist_avg_amount",
    "beh_hist_max_amount",
    "beh_hist_std_amount",
    "beh_amount_to_hist_avg_ratio",
    "beh_rolling_tx_count_1h",
    "beh_rolling_amount_1h",
    "beh_rolling_tx_count_24h",
    "beh_rolling_amount_24h",
    "beh_rolling_tx_count_7d",
    "beh_rolling_amount_7d",
    "beh_hist_unique_devices",
    "beh_hist_unique_ips",
    "beh_hist_unique_beneficiaries",
    "beh_is_new_device",
    "beh_is_new_ip",
    "beh_is_new_beneficiary",
]


class PointInTimeBehaviorExtractor:
    """Extracts point-in-time behavioral and velocity features per transaction."""

    COLUMNS = BEHAVIORAL_FEATURE_COLUMNS

    def __init__(self, df_accounts: pd.DataFrame):
        """Initialize with account metadata to resolve account_created_at."""
        self.account_created_map: Dict[str, pd.Timestamp] = {}
        for _, row in df_accounts.iterrows():
            aid = str(row["account_id"])
            created_ts = pd.to_datetime(row["account_created_at"], utc=True)
            self.account_created_map[aid] = created_ts

    def extract_features(self, df_transactions: pd.DataFrame) -> pd.DataFrame:
        """Extract point-in-time behavioral features for all transactions.
        
        Transactions are processed in strict chronological order per account.
        """
        # Ensure proper sorting by timestamp, then transaction_id
        df = df_transactions.copy()
        df["dt_timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df["num_amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
        df = df.sort_values(by=["dt_timestamp", "transaction_id"]).reset_index(drop=True)

        # Pre-group transactions by account_id for chronological state tracking
        account_groups = df.groupby("account_id")

        feature_records: List[Dict[str, Any]] = []

        for aid, group in account_groups:
            acc_created_at = self.account_created_map.get(aid)
            
            # Historical state tracking structures
            tx_history: List[Tuple[pd.Timestamp, float]] = []
            seen_devices: Set[str] = set()
            seen_ips: Set[str] = set()
            seen_beneficiaries: Set[str] = set()

            for seq_idx, (_, row) in enumerate(group.iterrows()):
                tx_id = str(row["transaction_id"])
                t_curr: pd.Timestamp = row["dt_timestamp"]
                amt_curr: float = float(row["num_amount"])
                dev_id = str(row["device_id"]) if pd.notna(row["device_id"]) else ""
                ip_id = str(row["ip_id"]) if pd.notna(row["ip_id"]) else ""
                ben_id = str(row["beneficiary_id"]).strip() if pd.notna(row["beneficiary_id"]) else ""

                # 1. Account age at transaction
                if acc_created_at is not None:
                    age_days = max(0.0, (t_curr - acc_created_at).total_seconds() / 86400.0)
                else:
                    age_days = 0.0

                # 2. Sequence & Time intervals
                seq_num = seq_idx + 1
                if seq_idx == 0:
                    time_since_last_sec = -1.0  # Sentinel for first transaction
                    is_first_tx = 1
                else:
                    t_prev = tx_history[-1][0]
                    time_since_last_sec = max(0.0, (t_curr - t_prev).total_seconds())
                    is_first_tx = 0

                # 3. Cumulative historical amounts (strictly t < T)
                if seq_idx == 0:
                    hist_count = 0
                    hist_total = 0.0
                    hist_avg = 0.0
                    hist_max = 0.0
                    hist_std = 0.0
                    ratio_to_avg = 1.0
                else:
                    prior_amts = [item[1] for item in tx_history]
                    hist_count = len(prior_amts)
                    hist_total = sum(prior_amts)
                    hist_avg = hist_total / hist_count
                    hist_max = max(prior_amts)
                    hist_std = float(np.std(prior_amts, ddof=1)) if hist_count > 1 else 0.0
                    ratio_to_avg = amt_curr / (hist_avg + 1e-5)

                # 4. Rolling time windows (strictly [t_curr - delta, t_curr))
                t_1h = t_curr - timedelta(hours=1)
                t_24h = t_curr - timedelta(hours=24)
                t_7d = t_curr - timedelta(days=7)

                # Filter prior transactions in window
                r1h = [amt for t, amt in tx_history if t >= t_1h]
                r24h = [amt for t, amt in tx_history if t >= t_24h]
                r7d = [amt for t, amt in tx_history if t >= t_7d]

                roll_count_1h = len(r1h)
                roll_amount_1h = sum(r1h)

                roll_count_24h = len(r24h)
                roll_amount_24h = sum(r24h)

                roll_count_7d = len(r7d)
                roll_amount_7d = sum(r7d)

                # 5. Endpoint novelty & diversity (strictly t < T)
                unique_dev_count = len(seen_devices)
                unique_ip_count = len(seen_ips)
                unique_ben_count = len(seen_beneficiaries)

                is_new_dev = 1 if (dev_id and dev_id not in seen_devices) else 0
                is_new_ip = 1 if (ip_id and ip_id not in seen_ips) else 0
                is_new_ben = 1 if (ben_id and ben_id not in seen_beneficiaries) else 0

                # Record feature row
                feature_records.append({
                    "transaction_id": tx_id,
                    "beh_account_age_days": round(age_days, 2),
                    "beh_tx_sequence_num": seq_num,
                    "beh_time_since_last_tx_sec": round(time_since_last_sec, 2),
                    "beh_is_first_tx": is_first_tx,
                    "beh_hist_tx_count": hist_count,
                    "beh_hist_total_amount": round(hist_total, 2),
                    "beh_hist_avg_amount": round(hist_avg, 2),
                    "beh_hist_max_amount": round(hist_max, 2),
                    "beh_hist_std_amount": round(hist_std, 2),
                    "beh_amount_to_hist_avg_ratio": round(ratio_to_avg, 4),
                    "beh_rolling_tx_count_1h": roll_count_1h,
                    "beh_rolling_amount_1h": round(roll_amount_1h, 2),
                    "beh_rolling_tx_count_24h": roll_count_24h,
                    "beh_rolling_amount_24h": round(roll_amount_24h, 2),
                    "beh_rolling_tx_count_7d": roll_count_7d,
                    "beh_rolling_amount_7d": round(roll_amount_7d, 2),
                    "beh_hist_unique_devices": unique_dev_count,
                    "beh_hist_unique_ips": unique_ip_count,
                    "beh_hist_unique_beneficiaries": unique_ben_count,
                    "beh_is_new_device": is_new_dev,
                    "beh_is_new_ip": is_new_ip,
                    "beh_is_new_beneficiary": is_new_ben,
                })

                # Update historical state WITH current transaction for subsequent transactions
                tx_history.append((t_curr, amt_curr))
                if dev_id:
                    seen_devices.add(dev_id)
                if ip_id:
                    seen_ips.add(ip_id)
                if ben_id:
                    seen_beneficiaries.add(ben_id)

        # Convert to DataFrame indexed by transaction_id
        res_df = pd.DataFrame(feature_records).set_index("transaction_id")
        
        # Ensure result aligns with input df_transactions order
        res_df = res_df.loc[df_transactions["transaction_id"].values]
        return res_df[BEHAVIORAL_FEATURE_COLUMNS]
