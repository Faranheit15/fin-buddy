"""Comprehensive tests for US-P04: Tenant authorization and account lifecycle."""

from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import Request

from app.api.deps import require_org_admin, require_org_owner
from app.api.v1.admin import set_user_role
from app.api.v1.emis import pay_installment_api
from app.core.config import Settings
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import AuthUser, get_current_user
from app.models.contact import Contact
from app.models.deleted_account import DeletedAccount
from app.models.emi import EmiInstallment, EmiPlan
from app.models.enums import (
    EmiInstallmentStatus,
    EmiPlanStatus,
    OrgRole,
    PlatformRole,
)
from app.models.organization import Organization, OrganizationMember
from app.models.profile import Profile
from app.services import (
    auth_service,
    emi_service,
    ledger_service,
    obligation_service,
    transaction_service,
    user_service,
)
from app.services.org_validators import (
    validate_account_in_org,
    validate_card_in_org,
    validate_category_in_org,
    validate_contact_in_org,
    validate_obligation_in_org,
    validate_statement_in_org,
    validate_transaction_in_org,
)


class _FakeResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value

    def scalar_one(self) -> object:
        return self._value

    def first(self) -> object:
        if isinstance(self._value, list):
            return self._value[0] if self._value else None
        return self._value

    def scalars(self) -> _FakeScalars:
        if isinstance(self._value, list):
            return _FakeScalars(self._value)
        return _FakeScalars([self._value] if self._value is not None else [])

    def all(self) -> list[object]:
        if isinstance(self._value, list):
            return self._value
        return [self._value] if self._value is not None else []


class _FakeScalars:
    def __init__(self, values: list[object]) -> None:
        self._values = values

    def all(self) -> list[object]:
        return self._values

    def first(self) -> object:
        return self._values[0] if self._values else None


class _MockSession:
    """Mock async session returning predetermined results."""

    def __init__(self, results: list[object] | None = None) -> None:
        self._results = list(results or [])
        self.added: list[object] = []
        self.deleted: list[object] = []
        self.committed = False

    async def execute(self, _stmt: object) -> _FakeResult:
        if not self._results:
            return _FakeResult(None)
        return _FakeResult(self._results.pop(0))

    async def scalar(self, _stmt: object) -> object:
        if not self._results:
            return None
        return self._results.pop(0)

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def delete(self, obj: object) -> None:
        self.deleted.append(obj)

    async def commit(self) -> None:
        self.committed = True

    async def flush(self) -> None:
        pass

    async def refresh(self, _obj: object) -> None:
        pass


# ==============================================================================
# 1. Migration 0016 Tests
# ==============================================================================


def _load_migration_0016() -> Any:
    migration_path = (
        Path(__file__).resolve().parent.parent
        / "alembic"
        / "versions"
        / "20260907_0016_tenant_authorization_and_lifecycle.py"
    )
    spec = importlib.util.spec_from_file_location("migration_20260907_0016", migration_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_0016_chain() -> None:
    mod = _load_migration_0016()
    assert mod.revision == "20260907_0016"
    assert mod.down_revision == "20260907_0015"


def test_migration_0016_audit_detects_inconsistent_data() -> None:
    mod = _load_migration_0016()
    mock_conn = MagicMock()
    mock_scalar = MagicMock(return_value=3)
    mock_conn.execute.return_value.scalar = mock_scalar

    with pytest.raises(RuntimeError) as exc:
        mod._audit_existing_rows(mock_conn)
    assert "found 3 cross-organization inconsistent row(s)" in str(exc.value)


def test_migration_0016_audit_passes_on_clean_data() -> None:
    mod = _load_migration_0016()
    mock_conn = MagicMock()
    mock_scalar = MagicMock(return_value=0)
    mock_conn.execute.return_value.scalar = mock_scalar

    # Should not raise
    mod._audit_existing_rows(mock_conn)
    assert mock_conn.execute.call_count == len(mod.PRE_AUDIT_CHECKS)


# ==============================================================================
# 2. Org Validators (Cross-Tenant Reference Validation)
# ==============================================================================


@pytest.mark.asyncio
async def test_validate_contact_in_org_success_and_foreign() -> None:
    my_org = uuid4()
    foreign_org = uuid4()
    contact_id = uuid4()

    # Success case: contact exists and matches org
    contact = Contact(id=contact_id, organization_id=my_org, name="Alice")
    session = _MockSession([contact])
    res = await validate_contact_in_org(session, my_org, contact_id)  # type: ignore[arg-type]
    assert res.id == contact_id

    # Cross-org / not found: contact doesn't match org query
    session_foreign = _MockSession([None])
    with pytest.raises(NotFoundError) as exc:
        await validate_contact_in_org(session_foreign, foreign_org, contact_id)  # type: ignore[arg-type]
    assert exc.value.code == "not_found"


@pytest.mark.asyncio
async def test_validate_card_in_org_foreign() -> None:
    my_org = uuid4()
    card_id = uuid4()
    session = _MockSession([None])

    with pytest.raises(NotFoundError) as exc:
        await validate_card_in_org(session, my_org, card_id)  # type: ignore[arg-type]
    assert exc.value.code == "not_found"


@pytest.mark.asyncio
async def test_validate_account_in_org_foreign() -> None:
    my_org = uuid4()
    account_id = uuid4()
    session = _MockSession([None])

    with pytest.raises(NotFoundError) as exc:
        await validate_account_in_org(session, my_org, account_id)  # type: ignore[arg-type]
    assert exc.value.code == "not_found"


@pytest.mark.asyncio
async def test_validate_category_in_org_foreign() -> None:
    my_org = uuid4()
    category_id = uuid4()
    session = _MockSession([None])

    with pytest.raises(NotFoundError) as exc:
        await validate_category_in_org(session, my_org, category_id)  # type: ignore[arg-type]
    assert exc.value.code == "not_found"


@pytest.mark.asyncio
async def test_validate_transaction_in_org_foreign() -> None:
    my_org = uuid4()
    tx_id = uuid4()
    session = _MockSession([None])

    with pytest.raises(NotFoundError) as exc:
        await validate_transaction_in_org(session, my_org, tx_id)  # type: ignore[arg-type]
    assert exc.value.code == "not_found"


@pytest.mark.asyncio
async def test_validate_obligation_in_org_foreign() -> None:
    my_org = uuid4()
    ob_id = uuid4()
    session = _MockSession([None])

    with pytest.raises(NotFoundError) as exc:
        await validate_obligation_in_org(session, my_org, ob_id)  # type: ignore[arg-type]
    assert exc.value.code == "not_found"


@pytest.mark.asyncio
async def test_validate_statement_in_org_foreign() -> None:
    my_org = uuid4()
    stmt_id = uuid4()
    session = _MockSession([None])

    with pytest.raises(NotFoundError) as exc:
        await validate_statement_in_org(session, my_org, stmt_id)  # type: ignore[arg-type]
    assert exc.value.code == "not_found"


# ==============================================================================
# 3. Role & Capability Enforcement (UI-06 Tiered Collaborative Hybrid)
# ==============================================================================


@pytest.mark.asyncio
async def test_require_org_admin_allows_admin_and_owner() -> None:
    org = Organization(id=uuid4(), name="Household")

    admin_member = OrganizationMember(
        id=uuid4(), organization_id=org.id, user_id=uuid4(), role=OrgRole.ADMIN
    )
    admin_ctx = (org, admin_member)
    assert await require_org_admin(admin_ctx) == admin_ctx

    owner_member = OrganizationMember(
        id=uuid4(), organization_id=org.id, user_id=uuid4(), role=OrgRole.OWNER
    )
    owner_ctx = (org, owner_member)
    assert await require_org_admin(owner_ctx) == owner_ctx


@pytest.mark.asyncio
async def test_require_org_admin_rejects_member() -> None:
    org = Organization(id=uuid4(), name="Household")
    member = OrganizationMember(
        id=uuid4(), organization_id=org.id, user_id=uuid4(), role=OrgRole.MEMBER
    )
    member_ctx = (org, member)

    with pytest.raises(ForbiddenError) as exc:
        await require_org_admin(member_ctx)
    assert exc.value.code == "forbidden"


@pytest.mark.asyncio
async def test_require_org_owner_allows_owner_only() -> None:
    org = Organization(id=uuid4(), name="Household")
    owner_member = OrganizationMember(
        id=uuid4(), organization_id=org.id, user_id=uuid4(), role=OrgRole.OWNER
    )
    owner_ctx = (org, owner_member)
    assert await require_org_owner(owner_ctx) == owner_ctx

    admin_member = OrganizationMember(
        id=uuid4(), organization_id=org.id, user_id=uuid4(), role=OrgRole.ADMIN
    )
    admin_ctx = (org, admin_member)
    with pytest.raises(ForbiddenError) as exc:
        await require_org_owner(admin_ctx)
    assert exc.value.code == "forbidden"


# ==============================================================================
# 4. Super Admin Demotion Protection
# ==============================================================================


@pytest.mark.asyncio
async def test_cannot_demote_last_super_admin() -> None:
    admin_id = uuid4()
    current_admin = AuthUser(
        id=admin_id,
        email="admin@finbuddy.test",
        phone=None,
        platform_role=PlatformRole.SUPER_ADMIN,
        raw_claims={},
    )
    profile = Profile(
        id=admin_id,
        platform_role=PlatformRole.SUPER_ADMIN,
        is_active=True,
        created_at=datetime.now(UTC),
    )
    req = MagicMock(spec=Request)

    # Session returns:
    # 1. target profile (super_admin)
    # 2. count of super_admins = 1
    session = _MockSession([profile, 1])

    with pytest.raises(ForbiddenError) as exc:
        await set_user_role(
            user_id=admin_id,
            request=req,
            db=session,  # type: ignore[arg-type]
            admin=current_admin,
            role=PlatformRole.USER,
        )
    assert "last remaining super_admin" in exc.value.message


@pytest.mark.asyncio
async def test_demoting_super_admin_succeeds_when_others_remain() -> None:
    admin_id = uuid4()
    current_admin = AuthUser(
        id=uuid4(),
        email="other_admin@finbuddy.test",
        phone=None,
        platform_role=PlatformRole.SUPER_ADMIN,
        raw_claims={},
    )
    profile = Profile(
        id=admin_id,
        platform_role=PlatformRole.SUPER_ADMIN,
        is_active=True,
        created_at=datetime.now(UTC),
    )
    req = MagicMock(spec=Request)

    # Session returns:
    # 1. target profile (super_admin)
    # 2. count of super_admins = 2 (safe to demote)
    session = _MockSession([profile, 2])

    with patch("app.api.v1.admin.log_activity", new_callable=AsyncMock):
        res = await set_user_role(
            user_id=admin_id,
            request=req,
            db=session,  # type: ignore[arg-type]
            admin=current_admin,
            role=PlatformRole.USER,
        )
    assert res.platform_role == PlatformRole.USER


# ==============================================================================
# 5. Account Deletion & Tombstone Lifecycle
# ==============================================================================


@pytest.mark.asyncio
async def test_get_current_user_rejects_deleted_tombstone() -> None:
    from fastapi.security import HTTPAuthorizationCredentials

    uid = uuid4()
    tombstone = DeletedAccount(user_id=uid, provider_deleted=True)
    session = _MockSession([None, tombstone])

    token_payload = {
        "sub": str(uid),
        "email": "deleted@example.com",
    }
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="valid-looking-jwt"
    )

    with patch("app.core.security.decode_supabase_jwt", return_value=token_payload):
        with pytest.raises(UnauthorizedError) as exc:
            await get_current_user(
                credentials=credentials,
                settings=Settings(),
                db=session,  # type: ignore[arg-type]
            )
        assert "Account has been deleted" in exc.value.message


@pytest.mark.asyncio
async def test_ensure_profile_and_org_rejects_deleted_account() -> None:
    uid = uuid4()
    tombstone = DeletedAccount(user_id=uid, provider_deleted=True)
    session = _MockSession([None, tombstone])

    with pytest.raises(UnauthorizedError) as exc:
        await user_service.ensure_profile_and_org(
            session,  # type: ignore[arg-type]
            user_id=uid,
            email="deleted@example.com",
            phone=None,
            display_name=None,
            avatar_url=None,
            settings=Settings(),
        )
    assert "Account has been deleted" in exc.value.message


@pytest.mark.asyncio
async def test_auth_bootstrap_rejects_deleted_account() -> None:
    from app.models.enums import ActivityAction

    uid = uuid4()
    tombstone = DeletedAccount(user_id=uid, provider_deleted=True)
    session = _MockSession([tombstone])

    auth_data = {
        "user": {"id": str(uid), "email": "deleted@example.com"},
        "access_token": "token",
        "refresh_token": "refresh",
        "expires_in": 3600,
        "token_type": "bearer",
    }

    with pytest.raises(UnauthorizedError) as exc:
        await auth_service._bootstrap_from_auth_response(
            session,  # type: ignore[arg-type]
            auth_data,
            Settings(),
            ip_address=None,
            user_agent=None,
            action=ActivityAction.LOGIN,
        )
    assert "Account has been deleted" in exc.value.message


@pytest.mark.asyncio
async def test_delete_account_provider_failure_retains_tombstone_and_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.exceptions import AppError

    uid = uuid4()
    org_id = uuid4()
    org = Organization(id=org_id, name="Test")
    profile = Profile(id=uid)

    call_count = 0

    class FailingSupabaseClient:
        def __init__(self, _settings: object) -> None:
            pass

        async def admin_delete_user(self, _user_id: UUID) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Supabase provider temporary 503 error")
            # Second call succeeds

    monkeypatch.setattr("app.services.auth_service.SupabaseAuthClient", FailingSupabaseClient)

    # First attempt: deletion fails at provider
    session1 = _MockSession([None, [org], [profile]])
    with pytest.raises(AppError) as exc:
        await auth_service.delete_account(session1, Settings(), uid)  # type: ignore[arg-type]
    assert exc.value.code == "provider_deletion_failed"

    # Tombstone was created with provider_deleted=False
    added_tombstones = [obj for obj in session1.added if isinstance(obj, DeletedAccount)]
    assert len(added_tombstones) == 1
    tomb = added_tombstones[0]
    assert tomb.user_id == uid
    assert tomb.provider_deleted is False

    # Second attempt (retry): session returns the existing tombstone
    session2 = _MockSession([tomb])
    await auth_service.delete_account(session2, Settings(), uid)  # type: ignore[arg-type]
    assert tomb.provider_deleted is True
    assert call_count == 2


# ==============================================================================
# 6. EMI Actor ID Fix
# ==============================================================================


@pytest.mark.asyncio
@patch("app.services.transaction_service.create_transaction")
async def test_pay_emi_installment_uses_actor_profile_id(
    mock_create_tx: AsyncMock,
) -> None:
    org_id = uuid4()
    card_id = uuid4()
    plan_id = uuid4()
    inst_id = uuid4()
    actor_user_id = uuid4()  # profile.id

    plan = EmiPlan(
        id=plan_id,
        organization_id=org_id,
        credit_card_id=card_id,
        principal_paise=10000_00,
        interest_rate_bps=1200,
        tenure_months=3,
        status=EmiPlanStatus.ACTIVE,
    )
    inst = EmiInstallment(
        id=inst_id,
        plan_id=plan_id,
        sequence_number=1,
        due_date=datetime.now(UTC).date(),
        principal_paise=3300_00,
        interest_paise=100_00,
        gst_paise=18_00,
        fees_paise=0,
        total_paise=3418_00,
        status=EmiInstallmentStatus.PENDING,
    )

    session = _MockSession([[(inst, plan)], [2]])

    await emi_service.pay_emi_installment(
        session,  # type: ignore[arg-type]
        organization_id=org_id,
        user_id=actor_user_id,
        installment_id=inst_id,
    )

    # Check that create_transaction received actor_user_id as user_id
    assert mock_create_tx.call_count == 2
    for call in mock_create_tx.call_args_list:
        assert call.kwargs["user_id"] == actor_user_id


@pytest.mark.asyncio
@patch("app.api.v1.emis.pay_emi_installment")
async def test_pay_installment_api_passes_current_user_profile_id(
    mock_service: AsyncMock,
) -> None:
    org_id = uuid4()
    member_id = uuid4()
    profile_id = uuid4()
    inst_id = uuid4()

    org = Organization(id=org_id, name="Household")
    member = OrganizationMember(
        id=member_id, organization_id=org_id, user_id=profile_id, role=OrgRole.MEMBER
    )
    org_ctx = (org, member)

    current_user = AuthUser(
        id=profile_id,
        email="actor@example.com",
        phone=None,
        platform_role=PlatformRole.USER,
        raw_claims={},
    )

    fake_installment = EmiInstallment(
        id=inst_id,
        plan_id=uuid4(),
        sequence_number=1,
        due_date=datetime.now(UTC).date(),
        principal_paise=1000,
        interest_paise=100,
        gst_paise=18,
        fees_paise=0,
        total_paise=1118,
        status=EmiInstallmentStatus.PAID,
    )
    mock_service.return_value = fake_installment

    session = _MockSession([])
    req = MagicMock(spec=Request)
    req.client = None
    req.headers = {}

    await pay_installment_api(
        installment_id=inst_id,
        request=req,
        db=session,  # type: ignore[arg-type]
        user=current_user,
        org_ctx=org_ctx,
    )

    # Critical check: verify user_id passed to service is profile_id, NOT member_id!
    mock_service.assert_awaited_once_with(
        session,
        organization_id=org_id,
        user_id=profile_id,
        installment_id=inst_id,
        ip=None,
        ua=None,
    )
    assert mock_service.call_args.kwargs["user_id"] == profile_id
    assert mock_service.call_args.kwargs["user_id"] != member_id


# ==============================================================================
# 7. Ledger Balance Organization Scoping
# ==============================================================================


@pytest.mark.asyncio
async def test_ledger_balance_functions_support_organization_id() -> None:
    session = _MockSession([5000_00])
    card_bal = await ledger_service.card_outstanding_paise(
        session,  # type: ignore[arg-type]
        card_id=uuid4(),
        organization_id=uuid4(),
    )
    assert card_bal == 5000_00

    session_acc = _MockSession([10000_00])
    acc_bal = await ledger_service.account_balance_paise(
        session_acc,  # type: ignore[arg-type]
        account_id=uuid4(),
        organization_id=uuid4(),
    )
    assert acc_bal == 10000_00

    session_contact = _MockSession([8000_00, 3000_00])
    contact_bal = await ledger_service.contact_balance_paise(
        session_contact,  # type: ignore[arg-type]
        contact_id=uuid4(),
        organization_id=uuid4(),
    )
    assert contact_bal == 5000_00


# ==============================================================================
# 8. Cross-Organization Reference Rejection at Service & Route Boundaries
# ==============================================================================


@pytest.mark.asyncio
async def test_create_transaction_rejects_cross_org_category() -> None:
    from app.models.enums import TransactionType

    org_id = uuid4()
    foreign_category_id = uuid4()
    user_id = uuid4()
    session = _MockSession([None])  # validate_category_in_org returns None -> NotFoundError

    with pytest.raises(NotFoundError) as exc:
        await transaction_service.create_transaction(
            session,  # type: ignore[arg-type]
            organization_id=org_id,
            user_id=user_id,
            credit_card_id=uuid4(),
            tx_type=TransactionType.PURCHASE,
            category_id=foreign_category_id,
            amount_paise=100_00,
            occurred_at=datetime.now(UTC),
            merchant="Coffee Shop",
        )
    assert exc.value.code == "not_found"
    assert "Category not found" in exc.value.message


@pytest.mark.asyncio
async def test_obligation_add_payment_rejects_cross_org_account() -> None:
    org_id = uuid4()
    user_id = uuid4()
    ob_id = uuid4()
    foreign_account_id = uuid4()
    session = _MockSession([None])  # validate_account_in_org returns None -> NotFoundError

    with pytest.raises(NotFoundError) as exc:
        await obligation_service.add_payment(
            session,  # type: ignore[arg-type]
            organization_id=org_id,
            user_id=user_id,
            obligation_id=ob_id,
            amount_paise=500_00,
            date=datetime.now(UTC),
            account_id=foreign_account_id,
        )
    assert exc.value.code == "not_found"
    assert "Account not found" in exc.value.message


@pytest.mark.asyncio
async def test_create_card_rejects_cross_org_contact() -> None:
    from app.api.v1.cards import create_card
    from app.models.enums import CardNetwork, DueRuleType
    from app.schemas.domain import CreditCardCreate

    org_id = uuid4()
    foreign_contact_id = uuid4()
    user_id = uuid4()

    org = Organization(id=org_id, name="Household")
    member = OrganizationMember(
        id=uuid4(), organization_id=org_id, user_id=user_id, role=OrgRole.ADMIN
    )
    admin_ctx = (org, member)
    user = AuthUser(
        id=user_id,
        email="admin@example.com",
        phone=None,
        platform_role=PlatformRole.USER,
        raw_claims={},
    )
    body = CreditCardCreate(
        nickname="Test Card",
        issuer="HDFC",
        network=CardNetwork.VISA,
        last_four="1234",
        credit_limit_paise=100000_00,
        currency="INR",
        statement_day=1,
        due_rule_type=DueRuleType.DAYS_AFTER_STATEMENT,
        due_rule_value=20,
        held_by_contact_id=foreign_contact_id,
    )
    session = _MockSession([None])  # validate_contact_in_org returns None
    req = MagicMock(spec=Request)

    with pytest.raises(NotFoundError) as exc:
        await create_card(
            body=body,
            request=req,
            db=session,  # type: ignore[arg-type]
            user=user,
            org_ctx=admin_ctx,
        )
    assert exc.value.code == "not_found"
    assert "Contact not found" in exc.value.message


@pytest.mark.asyncio
async def test_create_settlement_rejects_cross_org_contact() -> None:
    from app.api.v1.settlements import create_settlement
    from app.models.enums import SettlementMethod
    from app.schemas.domain import SettlementCreate

    org_id = uuid4()
    foreign_contact_id = uuid4()
    user_id = uuid4()

    org = Organization(id=org_id, name="Household")
    member = OrganizationMember(
        id=uuid4(), organization_id=org_id, user_id=user_id, role=OrgRole.MEMBER
    )
    org_ctx = (org, member)
    user = AuthUser(
        id=user_id,
        email="member@example.com",
        phone=None,
        platform_role=PlatformRole.USER,
        raw_claims={},
    )
    body = SettlementCreate(
        contact_id=foreign_contact_id,
        amount_paise=1000_00,
        currency="INR",
        method=SettlementMethod.UPI,
        settled_at=datetime.now(UTC),
    )
    session = _MockSession([None])  # contact query returns None
    req = MagicMock(spec=Request)

    with pytest.raises(NotFoundError) as exc:
        await create_settlement(
            body=body,
            request=req,
            db=session,  # type: ignore[arg-type]
            user=user,
            org_ctx=org_ctx,
        )
    assert exc.value.code == "not_found"
    assert "Contact not found" in exc.value.message
