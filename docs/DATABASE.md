# RingGuard AI — PostgreSQL Database Specification & Guide

> **Stage 3: PostgreSQL Database**  
> *Authoritative Relational Persistence Layer for RingGuard AI*

---

## 1. Overview & Architecture

In Stage 3, RingGuard AI establishes a persistent, relational source of truth using **PostgreSQL 18** and **SQLAlchemy 2.0**. The database stores the synthetic payment-risk dataset generated in Stage 2 (`ml/data/generated/`) with complete relational integrity, exact decimal financial precision, timezone-aware chronology, and synthetic provenance metadata.

---

## 2. Environment & Connection Setup

### Local Development Environment
- **RDBMS Engine:** PostgreSQL 18.6
- **Service Name:** `postgresql-x64-18`
- **Default Port:** `6207` (or standard `5432`)
- **Python Driver:** `psycopg2-binary` (v2.9.12)
- **ORM / Toolkit:** `SQLAlchemy` (v2.0.52)
- **Migration Framework:** `Alembic` (v1.19.1)

### Environment Variable (`.env`)
The database connection string is loaded via the project's gitignored `.env` file:
```env
DATABASE_URL=postgresql+psycopg2://postgres:<password>@localhost:6207/ringguard
```
> [!CAUTION]
> Never hardcode passwords or connection strings into source code, migration files, or documentation.

---

## 3. Relational Schema & Table Definitions

```
                     ┌──────────────────┐
                     │    customers     │
                     └────────┬─────────┘
                              │ 1:N
                              ▼
                     ┌──────────────────┐
                     │     accounts     │
                     └────────┬─────────┘
                              │ 1:N
                              ▼
┌───────────────┐    ┌──────────────────┐    ┌───────────────────┐
│    devices    ├───►│   transactions   │◄───┤        ips        │
└───────────────┘    └────────┬─────────┘    └───────────────────┘
                              │
               ┌──────────────┴──────────────┐
           0..1│                             │0..1
               ▼                             ▼
       ┌───────────────┐             ┌───────────────┐
       │ beneficiaries │             │   merchants   │
       └───────────────┘             └───────────────┘
```

### Table Details

#### 1. `customers`
- `customer_id` (VARCHAR(32), Primary Key): Stable customer identifier.
- `customer_name` (VARCHAR(128), NOT NULL): Synthetic customer name.
- `customer_email` (VARCHAR(128), NOT NULL): Synthetic email.
- `customer_phone_hash` (VARCHAR(64), NOT NULL): Deterministic phone token.
- `risk_tier` (VARCHAR(32), NOT NULL): Tier indicator (`STANDARD`, `PREMIUM`, `LOW_ACTIVITY`).
- `created_at` (TIMESTAMPTZ, NOT NULL): Onboarding timestamp.

#### 2. `accounts`
- `account_id` (VARCHAR(32), Primary Key): Stable account identifier.
- `customer_id` (VARCHAR(32), Foreign Key -> `customers.customer_id`, ON DELETE CASCADE): Owning customer.
- `account_created_at` (TIMESTAMPTZ, NOT NULL): Creation timestamp.
- `account_status` (VARCHAR(32), NOT NULL): Status (`ACTIVE`, `RESTRICTED`, `DORMANT`).
- `account_type` (VARCHAR(32), NOT NULL): Type (`SAVINGS`, `CURRENT`, `WALLET`).
- `scenario_id` (VARCHAR(64), NOT NULL, Indexed): Controlled scenario cluster ID.
- `scenario_type` (VARCHAR(64), NOT NULL, Indexed): Scenario name.
- `ground_truth_label` (VARCHAR(32), NOT NULL, Indexed): Supervised label (`legitimate`, `ring`).

#### 3. `devices`
- `device_id` (VARCHAR(32), Primary Key): Endpoint hardware ID.
- `device_type` (VARCHAR(64), NOT NULL): Platform (`MOBILE_ANDROID`, `MOBILE_IOS`, `DESKTOP_WINDOWS`, `DESKTOP_MAC`).
- `device_created_at` (TIMESTAMPTZ, NOT NULL): Initial registration timestamp.
- `device_os` (VARCHAR(64), NOT NULL): OS version.
- `fingerprint_hash` (VARCHAR(64), NOT NULL): Hardware fingerprint token.

#### 4. `ips`
- `ip_id` (VARCHAR(32), Primary Key): Network IP record identifier.
- `ip_address` (VARCHAR(45), NOT NULL): Synthetic IP string.
- `ip_type` (VARCHAR(32), NOT NULL): Category (`RESIDENTIAL`, `CELLULAR`, `DATACENTER`, `VPN_PROXY`).
- `asn_org` (VARCHAR(128), NOT NULL): ISP / hosting provider name.
- `country` (VARCHAR(8), NOT NULL): Country code.

#### 5. `beneficiaries`
- `beneficiary_id` (VARCHAR(32), Primary Key): Destination recipient identifier.
- `beneficiary_type` (VARCHAR(64), NOT NULL): Type (`INDIVIDUAL_ACCOUNT`, `UPI_VPA`, `WALLET_MERCHANT`, `ESCROW_GATEWAY`).
- `bank_ifsc_prefix` (VARCHAR(16), NOT NULL): IFSC prefix.
- `account_hash` (VARCHAR(64), NOT NULL): Destination account token.

#### 6. `merchants`
- `merchant_id` (VARCHAR(32), Primary Key): Commercial entity identifier.
- `merchant_category` (VARCHAR(64), NOT NULL): Category (`ECOMMERCE`, `FOOD_GROCERY`, etc.).
- `merchant_name` (VARCHAR(128), NOT NULL): Commercial brand name.
- `merchant_risk_rating` (VARCHAR(32), NOT NULL): Risk level (`LOW`, `MEDIUM`, `ELEVATED`).

#### 7. `transactions`
- `transaction_id` (VARCHAR(32), Primary Key): Transaction identifier.
- `account_id` (VARCHAR(32), Foreign Key -> `accounts.account_id`, ON DELETE RESTRICT): Origin account.
- `beneficiary_id` (VARCHAR(32), Foreign Key -> `beneficiaries.beneficiary_id`, Nullable): Target recipient for P2P transfers.
- `merchant_id` (VARCHAR(32), Foreign Key -> `merchants.merchant_id`, Nullable): Target merchant for P2M payments.
- `device_id` (VARCHAR(32), Foreign Key -> `devices.device_id`, ON DELETE RESTRICT): Device used.
- `ip_id` (VARCHAR(32), Foreign Key -> `ips.ip_id`, ON DELETE RESTRICT): IP access point.
- `timestamp` (TIMESTAMPTZ, NOT NULL, Indexed): Execution timestamp (strictly >= account creation).
- `amount` (NUMERIC(14, 2), NOT NULL): Monetary amount with check constraint `CHECK (amount > 0)`.
- `transaction_type` (VARCHAR(32), NOT NULL): `TRANSFER_P2P` or `PAYMENT_P2M`.
- `status` (VARCHAR(32), NOT NULL): `SUCCESS`, `FAILED`, `PENDING`.
- `channel` (VARCHAR(32), NOT NULL): `UPI`, `IMPS`, `CARD`, `NETBANKING`.
- `scenario_id` (VARCHAR(64), NOT NULL, Indexed): Provenance cluster ID.
- `scenario_type` (VARCHAR(64), NOT NULL, Indexed): Scenario name.
- `ground_truth_label` (VARCHAR(32), NOT NULL, Indexed): Supervised label (`legitimate`, `ring`).

#### 8. `dataset_metadata`
- `metadata_id` (INTEGER, Primary Key, Auto-increment): Provenance record key.
- `dataset_name` (VARCHAR(64), NOT NULL): `ringguard_mvp_v1`.
- `dataset_version` (VARCHAR(32), NOT NULL): `1.0.0`.
- `generator_version` (VARCHAR(32), NOT NULL): `0.2.0`.
- `random_seed` (BIGINT, NOT NULL): `20260903`.
- `synthetic` (BOOLEAN, NOT NULL): `true`.
- `disclaimer` (TEXT, NOT NULL): Strict synthetic provenance notice.
- `imported_at` (TIMESTAMPTZ, NOT NULL): Database import timestamp.
- `entity_counts_json` (TEXT, Nullable): JSON record of entity row counts.
- `config_json` (TEXT, Nullable): JSON record of generator configuration.

---

## 4. Operational Commands

### 1. Migrations (Alembic)
```bash
# Apply migrations to bring schema to latest revision
alembic upgrade head

# Rollback migration if needed
alembic downgrade -1
```

### 2. Seed Pipeline
Import the Stage 2 CSV datasets from `ml/data/generated/`:
```bash
# Seed database (fails if data already exists to prevent duplicates)
python scripts/seed_database.py

# Safe clean reset and re-seed
python scripts/seed_database.py --reset
```

### 3. Database Validation
Verify that row counts match Stage 2 exactly, primary keys are unique, foreign keys resolve, and constraints hold:
```bash
python scripts/validate_database.py
```

### 4. Automated Tests
```bash
# Run database test suite
pytest backend/tests/test_database.py -v

# Run all backend tests
pytest backend/tests -v
```

---

## 5. Provenance & Limitations

- **Strictly Synthetic:** All data in PostgreSQL is synthetic generated data. It contains no real customer, transaction, or merchant data from Razorpay or banking partners.
- **Persistence Boundary:** In Stage 3, PostgreSQL serves as a data foundation. No active FastAPI query endpoints, ML models, or graph engines are mounted yet.
