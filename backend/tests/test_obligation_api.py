"""Unit tests for obligations API router."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import Request

from app.api.v1.obligations import create_obligation, delete_obligation
from app.core.exceptions import NotFoundError
from app.core.security import AuthUser
from app.models.enums import ObligationType, PlatformRole
from app.models.obligation import Obligation
from app.schemas.domain import ObligationCreate

class _FakeResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value


class _FakeSession:
    def __init__(self, results: list[object] | None = None) -> None:
        self._results = list(results or [])
        self.added: list[object] = []
        self.deleted: list[object] = []

    async def execute(self, _stmt: object) -> _FakeResult:
        if not self._results:
            return _FakeResult(None)
        return _FakeResult(self._results.pop(0))

    async def scalar(self, _stmt: object) -> object:
        if not self._results:
            return None
        res = self._results.pop(0)
        return res

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def delete(self, obj: object) -> None:
        self.deleted.append(obj)

    async def flush(self) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def refresh(self, obj: object) -> None:
        pass


@pytest.fixture
def fake_request() -> Request:
    req = MagicMock(spec=Request)
    req.client = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers = {"user-agent": "test-agent"}
    return req


def fake_user() -> AuthUser:
    return AuthUser(
        id=uuid4(),
        email="test@example.com",
        phone=None,
        platform_role=PlatformRole.USER,
        raw_claims={},
    )


@pytest.mark.asyncio
async def test_create_obligation_foreign_contact_id_raises_not_found(fake_request: Request) -> None:
    org_id = uuid4()
    org = MagicMock()
    org.id = org_id
    org_ctx = (org, MagicMock())
    user = fake_user()

    # DB returns None for contact lookup
    db = _FakeSession([None])

    body = ObligationCreate(
        contact_id=uuid4(),
        type=ObligationType.RECEIVABLE,
        amount_paise=1000_00,
    )

    with pytest.raises(NotFoundError) as exc:
        await create_obligation(
            body=body,
            request=fake_request,
            db=db,  # type: ignore[arg-type]
            user=user,
            org_ctx=org_ctx,
        )

    assert exc.value.code == "not_found"
    assert "Contact not found" in str(exc.value)


@pytest.mark.asyncio
async def test_delete_obligation_foreign_id_raises_not_found(fake_request: Request) -> None:
    org_id = uuid4()
    org = MagicMock()
    org.id = org_id
    org_ctx = (org, MagicMock())
    user = fake_user()

    # DB returns None for obligation lookup
    db = _FakeSession([None])

    with pytest.raises(NotFoundError) as exc:
        await delete_obligation(
            obligation_id=uuid4(),
            request=fake_request,
            db=db,  # type: ignore[arg-type]
            user=user,
            org_ctx=org_ctx,
        )

    assert exc.value.code == "not_found"
    assert "Obligation not found" in str(exc.value)


@pytest.mark.asyncio
async def test_delete_obligation_success(fake_request: Request) -> None:
    org_id = uuid4()
    obl_id = uuid4()
    org = MagicMock()
    org.id = org_id
    org_ctx = (org, MagicMock())
    user = fake_user()

    obl = Obligation(id=obl_id, organization_id=org_id)
    # DB returns obl for lookup
    db = _FakeSession([obl])

    await delete_obligation(
        obligation_id=obl_id,
        request=fake_request,
        db=db,  # type: ignore[arg-type]
        user=user,
        org_ctx=org_ctx,
    )

    assert len(db.deleted) == 1
    assert db.deleted[0] is obl

