"""Tests for user deletion endpoint."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.profile import Profile
from app.models.organization import Organization, OrganizationMember

class _FakeResult:
    def __init__(self, values: list[object] | object = None) -> None:
        if isinstance(values, list):
            self._values = values
        else:
            self._values = [values] if values is not None else []
            
    def scalar_one_or_none(self) -> object:
        if not self._values:
            return None
        return self._values[0]

    def scalars(self) -> "_FakeScalars":
        return _FakeScalars(self._values)

class _FakeScalars:
    def __init__(self, values: list[object]) -> None:
        self._values = values
    def all(self) -> list[object]:
        return self._values
    def first(self) -> object:
        if not self._values:
            return None
        return self._values[0]

class _RecordingSession:
    def __init__(self, results: list[object] | None = None) -> None:
        self._results = list(results or [])

    async def execute(self, _stmt: object) -> _FakeResult:
        if not self._results:
            return _FakeResult(None)
        res = self._results.pop(0)
        return _FakeResult(res)

    async def delete(self, _obj: object) -> None:
        pass
        
    async def commit(self) -> None:
        pass


@pytest.mark.asyncio
async def test_delete_me(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 1. Setup mock for SupabaseAuthClient
    delete_called_for = []
    
    class MockSupabaseClient:
        def __init__(self, settings):
            pass
        async def admin_delete_user(self, user_id):
            delete_called_for.append(user_id)
            
    monkeypatch.setattr("app.services.auth_service.SupabaseAuthClient", MockSupabaseClient)
    
    uid = uuid4()
    org_id = uuid4()
    org = Organization(id=org_id, name="Test")
    profile = Profile(id=uid)
    
    db = _RecordingSession([
        # 1. select orgs
        [org],
        # 2. select profile
        [profile]
    ])

    from app.services.auth_service import delete_account
    from app.core.config import Settings
    
    await delete_account(db, Settings(), uid) # type: ignore[arg-type]
        
    # 5. Verify supabase client called
    assert uid in delete_called_for
