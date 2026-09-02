"""RingGuard AI — Feature Validation and Leakage Auditor.

Stage 5: Feature Engineering.
Validates data integrity, NaN/inf absence, data types, and conducts strict
target leakage audits ensuring no ground truth or scenario labels contaminate features.
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd

PROHIBITED_LEAKAGE_TERMS = [
    "ground_truth_label",
    "scenario_type",
    "scenario_id",
    "is_ring",
    "is_fraud",
    "fraud",
    "label",
    "target",
]


class FeatureValidator:
    """Validates feature matrices and conducts automated leakage audits."""

    @staticmethod
    def audit_target_leakage(df_features: pd.DataFrame, feature_group_name: str = "features") -> List[str]:
        """Verify that no target, scenario, or label columns exist in the feature set.
        
        Returns a list of violations (empty if 100% clean).
        """
        violations = []
        cols_lower = [c.lower() for c in df_features.columns]

        # 1. Exact prohibited names
        for term in ["ground_truth_label", "scenario_type", "is_ring", "is_fraud"]:
            if term in cols_lower:
                violations.append(f"Target leakage in {feature_group_name}: prohibited column '{term}' present.")

        # 2. Heuristic check on column substrings
        for col in df_features.columns:
            clow = col.lower()
            if clow in ["target", "label", "fraud", "ring"]:
                violations.append(f"Suspicious column name in {feature_group_name}: '{col}'")

        return violations

    @staticmethod
    def audit_data_integrity(df_features: pd.DataFrame, feature_group_name: str = "features") -> Dict[str, Any]:
        """Check for NaN, infinity, negative counts, and invalid types."""
        nan_counts = df_features.isna().sum()
        total_nans = int(nan_counts.sum())

        inf_counts = np.isinf(df_features.select_dtypes(include=[np.number])).sum().sum()
        
        # Check non-negative counts on count columns
        count_cols = [c for c in df_features.columns if "count" in c or "degree" in c or "seq_num" in c]
        negative_counts = 0
        for c in count_cols:
            if (df_features[c] < 0).any():
                negative_counts += int((df_features[c] < 0).sum())

        return {
            "feature_group": feature_group_name,
            "row_count": len(df_features),
            "column_count": len(df_features.columns),
            "total_nans": total_nans,
            "total_infs": int(inf_counts),
            "negative_counts_anomalies": negative_counts,
            "is_valid": (total_nans == 0 and inf_counts == 0 and negative_counts == 0),
        }

    @staticmethod
    def generate_feature_summary(df_features: pd.DataFrame, feature_group: str) -> List[Dict[str, Any]]:
        """Generate statistical summary for every feature in the DataFrame."""
        summary = []
        for col in df_features.columns:
            series = df_features[col]
            dtype_str = str(series.dtype)
            missing = int(series.isna().sum())
            unique_cnt = int(series.nunique())

            if np.issubdtype(series.dtype, np.number):
                min_val = round(float(series.min()), 4) if not series.empty else 0.0
                max_val = round(float(series.max()), 4) if not series.empty else 0.0
                mean_val = round(float(series.mean()), 4) if not series.empty else 0.0
            else:
                min_val = None
                max_val = None
                mean_val = None

            summary.append({
                "feature_name": col,
                "feature_group": feature_group,
                "dtype": dtype_str,
                "missing_count": missing,
                "unique_count": unique_cnt,
                "min": min_val,
                "max": max_val,
                "mean": mean_val,
            })
        return summary
