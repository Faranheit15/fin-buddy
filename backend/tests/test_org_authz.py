"""Organization scoping / authz unit tests."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.security import AuthUser
from app.models.enums import OrgRole, PlatformRole
from app.services.org_context import resolve_organization


class _FakeResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value


class _FakeSession:
    """Minimal async session stub that returns queued execute results."""

    def __init__(self, results: list[object]) -> None:
        self._results = list(results)

    async def execute(self, _stmt: object) -> _FakeResult:
        if not self._results:
            return _FakeResult(None)
        return _FakeResult(self._results.pop(0))


def _user() -> AuthUser:
    return AuthUser(
        id=uuid4(),
        email="owner@example.com",
        phone=None,
        platform_role=PlatformRole.USER,
        raw_claims={},
    )


@pytest.mark.asyncio
async def test_resolve_org_rejects_non_member() -> None:
    user = _user()
    foreign_org = uuid4()
    db = _FakeSession([None])  # no membership row

    with pytest.raises(ForbiddenError) as exc:
        await resolve_organization(db, user, foreign_org)  # type: ignore[arg-type]
    assert exc.value.code == "forbidden"


@pytest.mark.asyncio
async def test_resolve_org_rejects_user_with_no_memberships() -> None:
    user = _user()
    db = _FakeSession([None])  # default org lookup empty

    with pytest.raises(ForbiddenError):
        await resolve_organization(db, user, None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_resolve_org_happy_path_explicit_id() -> None:
    user = _user()
    org_id = uuid4()
    member = SimpleNamespace(
        user_id=user.id,
        organization_id=org_id,
        role=OrgRole.OWNER,
        created_at=datetime.now(UTC),
    )
    org = SimpleNamespace(id=org_id, name="Personal", slug="personal")
    db = _FakeSession([member, org])

    resolved_org, resolved_member = await resolve_organization(db, user, org_id)  # type: ignore[arg-type]
    assert resolved_org.id == org_id
    assert resolved_member.organization_id == org_id


@pytest.mark.asyncio
async def test_resolve_org_missing_org_row() -> None:
    user = _user()
    org_id = uuid4()
    member = SimpleNamespace(
        user_id=user.id,
        organization_id=org_id,
        role=OrgRole.MEMBER,
        created_at=datetime.now(UTC),
    )
    db = _FakeSession([member, None])

    with pytest.raises(NotFoundError):
        await resolve_organization(db, user, org_id)  # type: ignore[arg-type]
