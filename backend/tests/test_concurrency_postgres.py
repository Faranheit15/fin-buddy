"""Real PostgreSQL concurrency and idempotency test suite for US-P05.

Validates row-level locking, atomic transactions, idempotency replay, and race condition
safety against a real PostgreSQL instance (localhost:5433).
"""

import asyncio
import os
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from starlette.responses import Response

from app.core.exceptions import AppError, ConflictError
from app.core.idempotency import IDEMPOTENCY_REPLAYED_HEADER, execute_idempotent
from app.models.account import Account
from app.models.credit_card import CreditCard
from app.models.emi import EmiInstallment, EmiPlan
from app.models.enums import (
    AccountKind,
    CardNetwork,
    CardStatus,
    DueRuleType,
    EmiInstallmentStatus,
    EmiPlanStatus,
    LineReviewStatus,
    ObligationStatus,
    ObligationType,
    OrgRole,
    PostingStatus,
    StatementStatus,
    TransactionType,
)
from app.models.idempotency import IdempotencyRecord
from app.models.obligation import Obligation
from app.models.obligation_payment import ObligationPayment
from app.models.organization import Organization, OrganizationMember
from app.models.profile import Profile
from app.models.statement import Statement, StatementLineCandidate
from app.models.transaction import Transaction
from app.schemas.domain import TransactionResponse
from app.services import (
    emi_service,
    obligation_service,
    statement_service,
    transaction_service,
)

# Build test db URL safely from PG* environment variables or fallback
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASSWORD", "postgres")
PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5433")
PG_DB = os.getenv("PGDATABASE", "finbuddy_test")
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    f"postgresql+asyncpg://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}",
)


async def _can_connect() -> bool:
    try:
        engine = create_async_engine(TEST_DB_URL, pool_pre_ping=True)
        async with engine.connect() as conn:
            await conn.execute(select(1))
        await engine.dispose()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not asyncio.run(_can_connect()),
    reason=f"PostgreSQL test database not reachable at {PG_HOST}:{PG_PORT}/{PG_DB}",
)


@pytest.fixture
async def pg_engine():
    engine = create_async_engine(
        TEST_DB_URL,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(pg_engine):
    return async_sessionmaker(pg_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
async def test_org(session_factory) -> tuple[UUID, UUID]:
    """Creates a unique test organization and user profile."""
    org_id = uuid4()
    user_id = uuid4()
    async with session_factory() as db:
        user = Profile(
            id=user_id,
            email=f"tester-{user_id.hex[:8]}@example.com",
            display_name="Concurrency Tester",
        )
        db.add(user)
        org = Organization(id=org_id, name=f"Org-{org_id.hex[:8]}", slug=f"org-{org_id.hex[:8]}")
        db.add(org)
        member = OrganizationMember(
            id=uuid4(),
            organization_id=org_id,
            user_id=user_id,
            role=OrgRole.OWNER,
        )
        db.add(member)
        await db.commit()
    return org_id, user_id


@pytest.fixture
async def test_account(session_factory, test_org) -> Account:
    """Creates a funded bank account."""
    org_id, user_id = test_org
    async with session_factory() as db:
        account = Account(
            id=uuid4(),
            organization_id=org_id,
            kind=AccountKind.BANK,
            name="Checking",
            currency="INR",
        )
        db.add(account)
        await db.flush()

        # Seed opening balance transaction
        tx = Transaction(
            id=uuid4(),
            organization_id=org_id,
            account_id=account.id,
            type=TransactionType.OPENING_BALANCE,
            posting_status=PostingStatus.POSTED,
            amount_paise=10000_00,  # ₹10,000
            currency="INR",
            occurred_at=datetime.now(UTC),
            merchant="Opening Balance",
            created_by=user_id,
        )
        db.add(tx)
        await db.commit()
        await db.refresh(account)
        return account


# ---------------------------------------------------------------------------
# Test 1: Idempotency Key Validation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_idempotency_key_syntax_validation(session_factory, test_org) -> None:
    org_id, user_id = test_org
    async with session_factory() as db:
        async def _dummy():
            return 200, {"ok": True}

        # Key too short (< 16 chars)
        with pytest.raises(AppError) as exc1:
            await execute_idempotent(
                db,
                organization_id=org_id,
                user_id=user_id,
                idempotency_key="too-short",
                request_path="/api/v1/test",
                payload={},
                action=_dummy,
            )
        assert exc1.value.code == "invalid_idempotency_key"

        # Key too long (> 128 chars)
        with pytest.raises(AppError) as exc2:
            await execute_idempotent(
                db,
                organization_id=org_id,
                user_id=user_id,
                idempotency_key="x" * 129,
                request_path="/api/v1/test",
                payload={},
                action=_dummy,
            )
        assert exc2.value.code == "invalid_idempotency_key"


# ---------------------------------------------------------------------------
# Test 2: Idempotent Replay (Same Key & Payload)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_idempotency_replay_returns_cached_response(session_factory, test_org, test_account) -> None:
    org_id, user_id = test_org
    key = f"idemp-replay-{uuid4()}"
    action_counter = 0

    async with session_factory() as db:
        async def _action():
            nonlocal action_counter
            action_counter += 1
            tx = await transaction_service.create_transaction(
                db,
                organization_id=org_id,
                user_id=user_id,
                credit_card_id=None,
                account_id=test_account.id,
                tx_type=TransactionType.PURCHASE,
                amount_paise=500_00,
                occurred_at=datetime.now(UTC),
                merchant="Test Cafe",
                posting_status=PostingStatus.POSTED,
            )
            return 201, TransactionResponse.model_validate(tx)

        resp1 = Response()
        code1, res1 = await execute_idempotent(
            db,
            organization_id=org_id,
            user_id=user_id,
            idempotency_key=key,
            request_path="/api/v1/transactions",
            payload={"amount": 50000, "merchant": "Test Cafe"},
            action=_action,
            response=resp1,
            result_parser=TransactionResponse.model_validate,
        )
        assert code1 == 201
        assert action_counter == 1
        assert IDEMPOTENCY_REPLAYED_HEADER not in resp1.headers

    # Second invocation with same key and payload on a fresh session
    async with session_factory() as db2:
        resp2 = Response()
        code2, res2 = await execute_idempotent(
            db2,
            organization_id=org_id,
            user_id=user_id,
            idempotency_key=key,
            request_path="/api/v1/transactions",
            payload={"amount": 50000, "merchant": "Test Cafe"},
            action=_action,
            response=resp2,
            result_parser=TransactionResponse.model_validate,
        )
        assert code2 == 201
        assert res2.id == res1.id
        assert action_counter == 1  # Action was NOT executed again!
        assert resp2.headers[IDEMPOTENCY_REPLAYED_HEADER] == "true"

    # Verify in DB: exactly 1 transaction was created
    async with session_factory() as db3:
        tx_count = await db3.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.organization_id == org_id,
                Transaction.merchant == "Test Cafe",
            )
        )
        assert tx_count == 1


# ---------------------------------------------------------------------------
# Test 3: Idempotency Payload Mismatch Conflict
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_idempotency_payload_mismatch_raises_conflict(session_factory, test_org) -> None:
    org_id, user_id = test_org
    key = f"idemp-mismatch-{uuid4()}"

    async with session_factory() as db:
        async def _action():
            return 200, {"success": True}

        code, _ = await execute_idempotent(
            db,
            organization_id=org_id,
            user_id=user_id,
            idempotency_key=key,
            request_path="/api/v1/resource",
            payload={"amount": 100},
            action=_action,
        )
        assert code == 200

    # Call with same key but altered payload
    async with session_factory() as db2:
        with pytest.raises(ConflictError) as exc:
            await execute_idempotent(
                db2,
                organization_id=org_id,
                user_id=user_id,
                idempotency_key=key,
                request_path="/api/v1/resource",
                payload={"amount": 200},  # Payload changed!
                action=_action,
            )
        assert exc.value.code == "idempotency_payload_mismatch"


# ---------------------------------------------------------------------------
# Test 4: Concurrent Duplicate Transactions Race Condition
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_concurrent_duplicate_transactions_race(session_factory, test_org, test_account) -> None:
    org_id, user_id = test_org
    shared_key = f"race-tx-{uuid4()}"
    execution_count = 0

    async def _send_request():
        async with session_factory() as db:
            async def _action():
                nonlocal execution_count
                execution_count += 1
                # Small sleep to broaden race window
                await asyncio.sleep(0.05)
                tx = await transaction_service.create_transaction(
                    db,
                    organization_id=org_id,
                    user_id=user_id,
                    credit_card_id=None,
                    account_id=test_account.id,
                    tx_type=TransactionType.PURCHASE,
                    amount_paise=120_00,
                    occurred_at=datetime.now(UTC),
                    merchant="Race Merchant",
                    posting_status=PostingStatus.POSTED,
                )
                return 201, TransactionResponse.model_validate(tx)

            try:
                code, res = await execute_idempotent(
                    db,
                    organization_id=org_id,
                    user_id=user_id,
                    idempotency_key=shared_key,
                    request_path="/api/v1/transactions",
                    payload={"amount": 12000, "merchant": "Race Merchant"},
                    action=_action,
                    result_parser=TransactionResponse.model_validate,
                )
                return ("success", code, res.id)
            except ConflictError as e:
                return ("conflict", 409, str(e.code))

    # Fire 5 concurrent requests with identical key and payload
    results = await asyncio.gather(*[_send_request() for _ in range(5)])

    # At least 1 request successfully executes the action
    successes = [r for r in results if r[0] == "success"]
    assert len(successes) >= 1
    # All successful responses return the exact same transaction ID
    tx_ids = {r[2] for r in successes}
    assert len(tx_ids) == 1

    # Verify in DB: only 1 transaction and 1 idempotency record exists
    async with session_factory() as db:
        count = await db.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.organization_id == org_id,
                Transaction.merchant == "Race Merchant",
            )
        )
        assert count == 1

        rec_count = await db.scalar(
            select(func.count(IdempotencyRecord.id)).where(
                IdempotencyRecord.organization_id == org_id,
                IdempotencyRecord.idempotency_key == shared_key,
            )
        )
        assert rec_count == 1


# ---------------------------------------------------------------------------
# Test 5: Concurrent Duplicate Reversals
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_concurrent_reversals_race(session_factory, test_org, test_account) -> None:
    org_id, user_id = test_org

    # Create original posted transaction
    async with session_factory() as db:
        orig = await transaction_service.create_transaction(
            db,
            organization_id=org_id,
            user_id=user_id,
            credit_card_id=None,
            account_id=test_account.id,
            tx_type=TransactionType.PURCHASE,
            amount_paise=350_00,
            occurred_at=datetime.now(UTC),
            merchant="Reversible Item",
            posting_status=PostingStatus.POSTED,
        )
        await db.commit()
        orig_id = orig.id

    # 2 concurrent reversal attempts on separate DB sessions
    async def _reverse_worker():
        async with session_factory() as db:
            try:
                tx = await transaction_service.reverse_transaction(
                    db,
                    organization_id=org_id,
                    user_id=user_id,
                    transaction_id=orig_id,
                    reason="Customer returned goods",
                )
                await db.commit()
                return ("success", tx.id)
            except ConflictError as ce:
                await db.rollback()
                return ("conflict", str(ce))
            except AppError as ae:
                await db.rollback()
                return ("app_error", str(ae.code))

    res1, res2 = await asyncio.gather(_reverse_worker(), _reverse_worker())

    statuses = {res1[0], res2[0]}
    # Exactly one must succeed, and one must be rejected
    assert "success" in statuses
    assert len(statuses) == 2  # One success, one conflict/app_error

    # Verify in DB: exactly 1 reversal transaction with reverses_id == orig_id
    async with session_factory() as db:
        reversals = (
            await db.execute(
                select(Transaction).where(
                    Transaction.organization_id == org_id,
                    Transaction.reverses_id == orig_id,
                )
            )
        ).scalars().all()
        assert len(reversals) == 1


# ---------------------------------------------------------------------------
# Test 6: Concurrent EMI Installment Payments
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_concurrent_emi_installment_payments_race(session_factory, test_org) -> None:
    org_id, user_id = test_org

    # Set up credit card & EMI plan with 3 installments
    async with session_factory() as db:
        card = CreditCard(
            id=uuid4(),
            organization_id=org_id,
            nickname="Test Card",
            issuer="HDFC",
            network=CardNetwork.VISA,
            last_four="5555",
            credit_limit_paise=50000_00,
            currency="INR",
            statement_day=1,
            due_rule_type=DueRuleType.DAYS_AFTER_STATEMENT,
            due_rule_value=20,
            status=CardStatus.ACTIVE,
        )
        db.add(card)
        await db.flush()

        account = Account(
            id=uuid4(),
            organization_id=org_id,
            kind=AccountKind.CREDIT_CARD,
            name="Test Card Account",
            institution="HDFC",
            currency="INR",
            credit_card_id=card.id,
        )
        db.add(account)

        plan = EmiPlan(
            id=uuid4(),
            organization_id=org_id,
            credit_card_id=card.id,
            principal_paise=3000_00,
            interest_rate_bps=1200,
            tenure_months=3,
            status=EmiPlanStatus.ACTIVE,
        )
        db.add(plan)
        await db.flush()

        inst1 = EmiInstallment(
            id=uuid4(),
            plan_id=plan.id,
            sequence_number=1,
            due_date=date.today(),
            principal_paise=1000_00,
            interest_paise=30_00,
            fees_paise=0,
            gst_paise=5_40,
            total_paise=1035_40,
            status=EmiInstallmentStatus.PENDING,
        )
        db.add(inst1)
        await db.commit()
        inst_id = inst1.id

    # 2 concurrent attempts to pay installment 1
    async def _pay_worker():
        async with session_factory() as db:
            try:
                inst = await emi_service.pay_emi_installment(
                    db,
                    organization_id=org_id,
                    user_id=user_id,
                    installment_id=inst_id,
                )
                await db.commit()
                return ("success", inst.id)
            except ConflictError as ce:
                await db.rollback()
                return ("conflict", str(ce.code))

    res1, res2 = await asyncio.gather(_pay_worker(), _pay_worker())

    statuses = {res1[0], res2[0]}
    assert "success" in statuses
    assert "conflict" in statuses  # Second attempt caught by row lock + already paid check

    # Verify installment status in DB
    async with session_factory() as db:
        inst_db = await db.scalar(select(EmiInstallment).where(EmiInstallment.id == inst_id))
        assert inst_db.status == EmiInstallmentStatus.PAID

        # Verify only 1 set of EMI transactions created
        emi_txs = (
            await db.execute(
                select(Transaction).where(
                    Transaction.organization_id == org_id,
                    Transaction.type.in_([TransactionType.EMI_INTEREST, TransactionType.EMI_GST]),
                )
            )
        ).scalars().all()
        assert len(emi_txs) == 2  # 1 interest tx + 1 gst tx


# ---------------------------------------------------------------------------
# Test 7: Concurrent Obligation Payments
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_concurrent_obligation_payments_race(session_factory, test_org) -> None:
    org_id, user_id = test_org

    # Create active obligation for ₹1,000
    async with session_factory() as db:
        obl = Obligation(
            id=uuid4(),
            organization_id=org_id,
            type=ObligationType.RECEIVABLE,
            amount_paise=1000_00,
            currency="INR",
            status=ObligationStatus.ACTIVE,
            counterparty_name="Alice",
            created_by=user_id,
        )
        db.add(obl)
        await db.commit()
        obl_id = obl.id

    # Two concurrent payments of ₹1,000 trying to pay the entire balance
    async def _pay_worker():
        async with session_factory() as db:
            try:
                payment = await obligation_service.add_payment(
                    db,
                    organization_id=org_id,
                    user_id=user_id,
                    obligation_id=obl_id,
                    amount_paise=1000_00,
                    date=datetime.now(UTC),
                )
                await db.commit()
                return ("success", payment.id)
            except ConflictError as ce:
                await db.rollback()
                return ("conflict", str(ce.code))

    res1, res2 = await asyncio.gather(_pay_worker(), _pay_worker())

    statuses = {res1[0], res2[0]}
    assert "success" in statuses
    assert "conflict" in statuses  # Second payment serialized by lock and rejected because already PAID

    # Verify in DB: exactly 1 payment recorded and obligation is PAID
    async with session_factory() as db:
        payments = (
            await db.execute(
                select(ObligationPayment).where(
                    ObligationPayment.obligation_id == obl_id,
                    ObligationPayment.organization_id == org_id,
                )
            )
        ).scalars().all()
        assert len(payments) == 1
        assert payments[0].amount_paise == 1000_00

        obl_db = await db.scalar(select(Obligation).where(Obligation.id == obl_id))
        assert obl_db.status == ObligationStatus.PAID


# ---------------------------------------------------------------------------
# Test 8: Concurrent Statement Imports
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_concurrent_statement_imports_race(session_factory, test_org) -> None:
    org_id, user_id = test_org

    # Create credit card and statement with 2 accepted candidate lines
    async with session_factory() as db:
        card = CreditCard(
            id=uuid4(),
            organization_id=org_id,
            nickname="Import Test Card",
            issuer="Axis",
            network=CardNetwork.MASTERCARD,
            last_four="9999",
            credit_limit_paise=20000_00,
            currency="INR",
            statement_day=5,
            due_rule_type=DueRuleType.DAYS_AFTER_STATEMENT,
            due_rule_value=20,
            status=CardStatus.ACTIVE,
        )
        db.add(card)
        await db.flush()

        acc = Account(
            id=uuid4(),
            organization_id=org_id,
            kind=AccountKind.CREDIT_CARD,
            name="Axis Card Account",
            institution="Axis",
            currency="INR",
            credit_card_id=card.id,
        )
        db.add(acc)

        stmt = Statement(
            id=uuid4(),
            organization_id=org_id,
            credit_card_id=card.id,
            pdf_storage_path="statements/test.txt",
            status=StatementStatus.NEEDS_REVIEW,
            created_by=user_id,
        )
        db.add(stmt)
        await db.flush()

        line1 = StatementLineCandidate(
            id=uuid4(),
            organization_id=org_id,
            statement_id=stmt.id,
            raw_payload={"raw": "2026-07-01|purchase|Swiggy|250.00"},
            occurred_at=datetime.now(UTC),
            merchant="Swiggy",
            amount_paise=250_00,
            proposed_type=TransactionType.PURCHASE,
            review_status=LineReviewStatus.ACCEPTED,
        )
        line2 = StatementLineCandidate(
            id=uuid4(),
            organization_id=org_id,
            statement_id=stmt.id,
            raw_payload={"raw": "2026-07-02|purchase|Uber|150.00"},
            occurred_at=datetime.now(UTC),
            merchant="Uber",
            amount_paise=150_00,
            proposed_type=TransactionType.PURCHASE,
            review_status=LineReviewStatus.ACCEPTED,
        )
        db.add_all([line1, line2])
        await db.commit()
        stmt_id = stmt.id

    # 2 concurrent workers attempting import confirm
    async def _import_worker():
        async with session_factory() as db:
            stmt_obj = await statement_service.get_statement_or_404(
                db, org_id, stmt_id, for_update=True
            )
            res = await statement_service.import_statement(
                db,
                statement=stmt_obj,
                user_id=user_id,
            )
            await db.commit()
            return res

    r1, r2 = await asyncio.gather(_import_worker(), _import_worker())

    # One worker created the 2 transactions, the second saw IMPORTED and created 0
    total_created = r1["created"] + r2["created"]
    assert total_created == 2

    # Verify statement status and candidate committed transactions in DB
    async with session_factory() as db:
        stmt_db = await db.scalar(select(Statement).where(Statement.id == stmt_id))
        assert stmt_db.status == StatementStatus.IMPORTED

        lines = (
            await db.execute(
                select(StatementLineCandidate).where(
                    StatementLineCandidate.statement_id == stmt_id,
                    StatementLineCandidate.organization_id == org_id,
                )
            )
        ).scalars().all()
        assert all(line.committed_transaction_id is not None for line in lines)

        # Ensure no duplicate transactions exist in transactions table
        txs = (
            await db.execute(
                select(Transaction).where(
                    Transaction.statement_id == stmt_id,
                    Transaction.organization_id == org_id,
                )
            )
        ).scalars().all()
        assert len(txs) == 2


# ---------------------------------------------------------------------------
# Test 9: Failure Before Commit Allows Subsequent Retry
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_failure_before_commit_allows_retry(session_factory, test_org) -> None:
    org_id, user_id = test_org
    retry_key = f"retry-fail-{uuid4()}"

    # First attempt fails mid-action
    async with session_factory() as db:
        async def _failing_action():
            raise RuntimeError("Database connection glitch or transient error")

        with pytest.raises(RuntimeError):
            await execute_idempotent(
                db,
                organization_id=org_id,
                user_id=user_id,
                idempotency_key=retry_key,
                request_path="/api/v1/flaky",
                payload={"attempt": 1},
                action=_failing_action,
            )

    # In DB: record was rolled back or is not COMPLETED
    async with session_factory() as db:
        rec = await db.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.organization_id == org_id,
                IdempotencyRecord.idempotency_key == retry_key,
            )
        )
        assert rec is None

    # Retry with same key now succeeds cleanly
    async with session_factory() as db2:
        async def _succeeding_action():
            return 200, {"status": "succeeded"}

        code, res = await execute_idempotent(
            db2,
            organization_id=org_id,
            user_id=user_id,
            idempotency_key=retry_key,
            request_path="/api/v1/flaky",
            payload={"attempt": 1},
            action=_succeeding_action,
        )
        assert code == 200
        assert res == {"status": "succeeded"}
