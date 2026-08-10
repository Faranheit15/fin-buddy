"""Operational-log retention tests."""

from typing import Any

import pytest

from app.services.retention_service import purge_operational_logs


class _RecordingSession:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    async def execute(self, statement: Any) -> None:
        self.statements.append(statement)


@pytest.mark.asyncio
async def test_retention_purges_every_operational_log_type() -> None:
    session = _RecordingSession()

    await purge_operational_logs(session, retention_days=90)  # type: ignore[arg-type]

    assert len(session.statements) == 3
