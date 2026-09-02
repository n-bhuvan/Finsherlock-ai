"""RingGuard AI — PostgreSQL Database Test Suite.

Stage 3: PostgreSQL Database.
Validates database connection, schema tables, constraint enforcement,
foreign-key integrity, transactional rollbacks, imported row counts,
scenario provenance fidelity, and synthetic metadata.
"""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal, get_engine
from app.models import (
    Customer,
    Account,
    Device,
    IPAddress,
    Beneficiary,
    Merchant,
    Transaction,
    DatasetMetadata,
)


@pytest.fixture(scope="module")
def db_session():
    """Module-level session for read-only assertions."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def transactional_session():
    """Function-level session wrapped in a transaction that always rolls back."""
    session = SessionLocal()
    session.begin_nested()
    yield session
    session.rollback()
    session.close()


# 1. Test database connection
def test_database_connection(db_session):
    result = db_session.execute(text("SELECT 1;")).scalar()
    assert result == 1


# 2. Test schema tables exist
def test_schema_tables_exist():
    engine = get_engine()
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    expected = {
        "customers",
        "accounts",
        "devices",
        "ips",
        "beneficiaries",
        "merchants",
        "transactions",
        "dataset_metadata",
    }
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"


# 3. Test customer insertion in rollback session
def test_customer_insertion(transactional_session):
    test_cust = Customer(
        customer_id="CUST_TEST_999999",
        customer_name="Test Customer",
        customer_email="test.customer@example.synth",
        customer_phone_hash="PH_TEST999999",
        risk_tier="STANDARD",
        created_at=datetime.now(timezone.utc),
    )
    transactional_session.add(test_cust)
    transactional_session.flush()

    retrieved = transactional_session.get(Customer, "CUST_TEST_999999")
    assert retrieved is not None
    assert retrieved.customer_name == "Test Customer"


# 4. Test account -> customer foreign key
def test_account_customer_foreign_key(transactional_session):
    test_acc = Account(
        account_id="ACC_TEST_999999",
        customer_id="CUST_NONEXISTENT_000",
        account_created_at=datetime.now(timezone.utc),
        account_status="ACTIVE",
        account_type="SAVINGS",
        scenario_id="SCEN_TEST",
        scenario_type="LEGITIMATE",
        ground_truth_label="legitimate",
    )
    transactional_session.add(test_acc)
    with pytest.raises(IntegrityError):
        transactional_session.flush()


# 5-9. Test transaction foreign keys (account, device, ip, beneficiary, merchant)
def test_transaction_foreign_keys_resolve(db_session):
    sample_tx = db_session.query(Transaction).first()
    assert sample_tx is not None
    assert sample_tx.account is not None
    assert sample_tx.device is not None
    assert sample_tx.ip is not None
    if sample_tx.beneficiary_id:
        assert sample_tx.beneficiary is not None
    if sample_tx.merchant_id:
        assert sample_tx.merchant is not None


# 10. Test positive transaction amount constraint (amount > 0)
def test_positive_transaction_amount_constraint(transactional_session):
    existing_acc = transactional_session.query(Account).first()
    existing_dev = transactional_session.query(Device).first()
    existing_ip = transactional_session.query(IPAddress).first()

    invalid_tx = Transaction(
        transaction_id="TXN_INVALID_AMT_001",
        account_id=existing_acc.account_id,
        device_id=existing_dev.device_id,
        ip_id=existing_ip.ip_id,
        timestamp=datetime.now(timezone.utc),
        amount=Decimal("-50.00"),  # Violates check constraint
        transaction_type="TRANSFER_P2P",
        status="SUCCESS",
        channel="UPI",
        scenario_id="SCEN_TEST",
        scenario_type="LEGITIMATE",
        ground_truth_label="legitimate",
    )
    transactional_session.add(invalid_tx)
    with pytest.raises(IntegrityError):
        transactional_session.flush()


# 11. Test duplicate primary key rejection
def test_duplicate_primary_key_rejection(transactional_session):
    existing_cust = transactional_session.query(Customer).first()
    dup_cust = Customer(
        customer_id=existing_cust.customer_id,  # Duplicate PK
        customer_name="Duplicate Name",
        customer_email="dup@example.synth",
        customer_phone_hash="PH_DUP",
        risk_tier="STANDARD",
        created_at=datetime.now(timezone.utc),
    )
    transactional_session.add(dup_cust)
    with pytest.raises(IntegrityError):
        transactional_session.flush()


# 12. Test invalid foreign key rejection on transaction
def test_invalid_foreign_key_rejection(transactional_session):
    existing_dev = transactional_session.query(Device).first()
    existing_ip = transactional_session.query(IPAddress).first()

    bad_tx = Transaction(
        transaction_id="TXN_BAD_FK_001",
        account_id="ACC_NONEXISTENT_999999",  # Invalid FK
        device_id=existing_dev.device_id,
        ip_id=existing_ip.ip_id,
        timestamp=datetime.now(timezone.utc),
        amount=Decimal("100.00"),
        transaction_type="TRANSFER_P2P",
        status="SUCCESS",
        channel="UPI",
        scenario_id="SCEN_TEST",
        scenario_type="LEGITIMATE",
        ground_truth_label="legitimate",
    )
    transactional_session.add(bad_tx)
    with pytest.raises(IntegrityError):
        transactional_session.flush()


# 13-14. Test full dataset imported row counts
def test_imported_row_counts(db_session):
    assert db_session.query(Customer).count() == 500
    assert db_session.query(Account).count() == 500
    assert db_session.query(Device).count() == 100
    assert db_session.query(IPAddress).count() == 150
    assert db_session.query(Beneficiary).count() == 100
    assert db_session.query(Merchant).count() == 50
    assert db_session.query(Transaction).count() == 2000
    assert db_session.query(DatasetMetadata).count() >= 1


# 15. Test scenario labels preserved
def test_scenario_labels_preserved(db_session):
    distinct_scenarios = {
        row[0] for row in db_session.query(Transaction.scenario_type).distinct().all()
    }
    expected_scenarios = {
        "LEGITIMATE",
        "SHARED_DEVICE_RING",
        "COMMON_BENEFICIARY_RING",
        "RAPID_FUND_DISTRIBUTION_RING",
        "HISTORICAL_CONNECTION_RING",
        "COMBINED_RING",
        "LEGITIMATE_LOOKALIKE",
    }
    assert expected_scenarios == distinct_scenarios


# 16. Test ground-truth labels preserved
def test_ground_truth_labels_preserved(db_session):
    distinct_labels = {
        row[0] for row in db_session.query(Transaction.ground_truth_label).distinct().all()
    }
    assert {"legitimate", "ring"}.issubset(distinct_labels)


# 17. Test synthetic provenance preserved
def test_synthetic_provenance_preserved(db_session):
    meta = db_session.query(DatasetMetadata).first()
    assert meta is not None
    assert meta.synthetic is True
    assert meta.random_seed == 20260903
    assert meta.dataset_name == "ringguard_mvp_v1"
    assert "synthetic" in meta.disclaimer.lower()
