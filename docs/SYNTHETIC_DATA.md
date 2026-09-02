# RingGuard AI — Synthetic Data Engine Specification

> [!CAUTION]
> **DATA PROVENANCE & STRICT DISCLAIMER**  
> This dataset is entirely synthetic and is **NOT** real Razorpay production data, customer data, or transaction data. It was algorithmically generated for research, architectural validation, model training, and defense-only risk investigation benchmarking for the Razorpay AI Buildathon 2026.

---

## 1. Why Synthetic Data Is Used

Developing fraud syndicate and payment abuse-ring detection systems presents unique data challenges:
1. **Privacy & Regulatory Compliance:** Real financial transaction logs contain sensitive Personally Identifiable Information (PII), bank account numbers, device identifiers, and payment credentials that cannot be utilized in open prototyping environments.
2. **Ground Truth Ambiguity in Real Data:** Real-world transaction logs rarely possess definitive ground truth for every coordinated mule network; many rings remain undiscovered or mislabeled.
3. **Controlled Experimental Benchmarking:** Evaluating graph algorithms (e.g., connected components, community detection) and machine learning models requires deterministic, parameterized scenarios where network topology and transaction velocities can be varied under reproducible conditions.

---

## 2. Dataset Entities & Relational Schemas

The generator models a relational financial operations graph saved as CSV files under `ml/data/generated/`:

### A. `customers.csv`
Represents the human or legal entities holding accounts:
- `customer_id` (Primary Key, e.g. `CUST_000001`)
- `customer_name`: Synthetic full name.
- `customer_email`: Synthetic email address.
- `customer_phone_hash`: SHA-256 masked phone identifier.
- `risk_tier`: `STANDARD`, `PREMIUM`, or `LOW_ACTIVITY`.
- `created_at`: ISO 8601 onboarding timestamp.

### B. `accounts.csv`
Represents payment/bank accounts owned by customers:
- `account_id` (Primary Key, e.g. `ACC_000001`)
- `customer_id` (Foreign Key -> `customers.customer_id`)
- `account_created_at`: ISO 8601 timestamp (strictly after customer creation).
- `account_status`: `ACTIVE`, `RESTRICTED`, or `DORMANT`.
- `account_type`: `SAVINGS`, `CURRENT`, or `WALLET`.
- `scenario_id`: Specific cluster identifier (e.g. `SCEN_SHARED_DEVICE_001`).
- `scenario_type`: Operational scenario name.
- `ground_truth_label`: Primary supervised label (`legitimate`, `suspicious`, `ring`).

### C. `devices.csv`
Represents hardware endpoints:
- `device_id` (Primary Key, e.g. `DEV_000001`)
- `device_type`: `MOBILE_ANDROID`, `MOBILE_IOS`, `DESKTOP_WINDOWS`, or `DESKTOP_MAC`.
- `device_created_at`: ISO 8601 timestamp.
- `device_os`: Operating system version.
- `fingerprint_hash`: Deterministic hardware fingerprint token.

### D. `ips.csv`
Represents network access points:
- `ip_id` (Primary Key, e.g. `IP_000001`)
- `ip_address`: Synthetic IP string.
- `ip_type`: `RESIDENTIAL`, `CELLULAR`, `DATACENTER`, or `VPN_PROXY`.
- `asn_org`: Telecommunications provider or hosting network.
- `country`: Two-letter ISO country code (`IN`, `SG`, `US`, etc.).

### E. `beneficiaries.csv`
Represents recipient endpoints for P2P/outbound transfers:
- `beneficiary_id` (Primary Key, e.g. `BEN_000001`)
- `beneficiary_type`: `INDIVIDUAL_ACCOUNT`, `UPI_VPA`, `WALLET_MERCHANT`, or `ESCROW_GATEWAY`.
- `bank_ifsc_prefix`: Indian financial system bank code prefix (`HDFC`, `SBIN`, `ICIC`, etc.).
- `account_hash`: Hashed beneficiary account token.

### F. `merchants.csv`
Represents commercial recipients for P2M payments:
- `merchant_id` (Primary Key, e.g. `MER_000001`)
- `merchant_name`: Synthetic business name.
- `merchant_category`: `ECOMMERCE`, `FOOD_GROCERY`, `UTILITIES_BILLS`, `TRAVEL_HOSPITALITY`, `GAMING_ENTERTAINMENT`, `FINANCIAL_SERVICES`, or `JEWELRY_LUXURY`.
- `merchant_risk_rating`: `LOW`, `MEDIUM`, or `ELEVATED`.

### G. `transactions.csv`
The core ledger of financial activities:
- `transaction_id` (Primary Key, e.g. `TXN_00000001`)
- `account_id` (Foreign Key -> `accounts.account_id`)
- `beneficiary_id` (Foreign Key -> `beneficiaries.beneficiary_id`, or empty if P2M)
- `merchant_id` (Foreign Key -> `merchants.merchant_id`, or empty if P2P)
- `device_id` (Foreign Key -> `devices.device_id`)
- `ip_id` (Foreign Key -> `ips.ip_id`)
- `timestamp`: ISO 8601 transaction timestamp (strictly >= `account_created_at`).
- `amount`: Monetary amount in INR (strictly positive).
- `transaction_type`: `TRANSFER_P2P` or `PAYMENT_P2M`.
- `status`: `SUCCESS`, `FAILED`, or `PENDING`.
- `channel`: `UPI`, `IMPS`, `NEFT`, `CARD`, or `NETBANKING`.
- `scenario_id`: Provenance cluster ID.
- `scenario_type`: Controlled scenario name.
- `ground_truth_label`: Ground truth label (`legitimate`, `suspicious`, `ring`).

---

## 3. Controlled Scenario Types

The generator creates 7 distinct, controlled operational scenarios:

| # | Scenario Name | Ground Truth Label | Topology & Behavioral Characteristics |
|---|---|---|---|
| 1 | `LEGITIMATE` | `legitimate` | Normal consumer spending, diverse merchants and recipients, standard diurnal cycles, independent devices/IPs. |
| 2 | `SHARED_DEVICE_RING` | `ring` | Multiple accounts from distinct customers operating from the exact same physical device (`device_id`) in rapid succession. |
| 3 | `COMMON_BENEFICIARY_RING` | `ring` | Unconnected accounts originating from distinct devices/IPs all channeling structured funds to a single common beneficiary (mule aggregator). |
| 4 | `RAPID_FUND_DISTRIBUTION_RING` | `ring` | High-velocity fan-out dispersion: accounts dispersing structured tranches to multiple recipients within minutes. |
| 5 | `HISTORICAL_CONNECTION_RING` | `ring` | Accounts that shared hardware/IPs weeks in the past that re-activate concurrently for coordinated transfers. |
| 6 | `COMBINED_RING` | `ring` | Multi-signal syndicate: shared device + VPN/hosting IP + common beneficiary + sub-minute micro-bursts + structured amounts. |
| 7 | `LEGITIMATE_LOOKALIKE` | `legitimate` | **Hard Negative:** Benign activities sharing attributes (family members sharing home tablet, employees sharing office IP, residents paying common landlord) with normal consumer spending patterns. |

---

## 4. Labeling Philosophy: No Single-Attribute Fraud

> [!IMPORTANT]
> **Core Labeling Rule:**  
> A shared device, shared IP, common beneficiary, or high velocity **alone** does not determine a fraud label. Real-world fraud risk requires evaluating compounding signals and behavioral context.
> 
> The `LEGITIMATE_LOOKALIKE` scenario enforces this by generating legitimate entities with shared infrastructure, preventing ML models from learning trivial, false-positive-prone rules like `shared_device == fraud`.

---

## 5. Reproducibility & Seed Configuration

The generator implements deterministic pseudorandom generation. When executed with the default seed (`20260903`) or any chosen seed, it produces **100% byte-identical** CSV datasets.

```bash
# Run with default seed (20260903)
python scripts/generate_data.py

# Run with custom seed and output directory
python scripts/generate_data.py --seed 42 --output-dir ml/data/custom_run
```

---

## 6. Output Artifacts

Running the generator produces:
- `ml/data/generated/customers.csv`
- `ml/data/generated/accounts.csv`
- `ml/data/generated/transactions.csv`
- `ml/data/generated/devices.csv`
- `ml/data/generated/ips.csv`
- `ml/data/generated/beneficiaries.csv`
- `ml/data/generated/merchants.csv`
- `ml/data/generated/scenario_summary.csv`: Cluster-level audit log of all generated scenarios.
- `ml/data/generated/dataset_metadata.json`: Provenance metadata with `synthetic: true`.
- `ml/data/generated/data_quality_report.txt`: Human-inspectable data quality audit report.

---

## 7. Data Quality & Validation Rules

The embedded validator enforces 13 strict integrity assertions prior to export:
1. **Non-Empty:** All tables contain records.
2. **Schema Fidelity:** All required columns exist.
3. **Primary Key Uniqueness:** Zero duplicate IDs in any table.
4. **Foreign Key Integrity:** 100% of transaction `account_id`, `device_id`, and `ip_id` exist.
5. **Conditional Reference Integrity:** Non-empty `beneficiary_id` and `merchant_id` resolve to existing entities.
6. **Positive Values:** All transaction amounts are strictly positive (`> 0`).
7. **Temporal Validity:** Transaction timestamps are valid ISO 8601 and occur after parent account creation.
8. **Label Validity:** All labels are in `['legitimate', 'suspicious', 'ring']`.
9. **Scenario Validity:** All scenarios match recognized scenario types.
10. **Synthetic Provenance:** Metadata declares `synthetic: true`.
11. **Missing Values:** Zero unexpected null values in mandatory fields.
12. **Reproducibility:** Seed produces deterministic output.
13. **Fail-Fast:** Generator halts and throws `ValidationException` if any check fails.

---

## 8. Limitations

- **Simulated Behavioral Dynamics:** Does not capture macro-economic shocks or regulatory policy shifts.
- **Statistical Approximations:** Device and IP distributions approximate regional fintech patterns rather than exhaustive global ISP topologies.
- **Defense-Only Scope:** Designed solely for testing detection and investigation capabilities; contains no live payment gateway or banking protocols.
