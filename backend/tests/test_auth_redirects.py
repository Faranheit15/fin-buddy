"""Authentication redirects must never be supplied by an untrusted client."""

import pytest

from app.core.config import Settings
from app.core.exceptions import AppError
from app.services.auth_service import _frontend_callback_url


def test_auth_redirect_accepts_only_the_configured_callback() -> None:
    settings = Settings(frontend_app_url="https://app.example.com")
    assert (
        _frontend_callback_url(settings, "https://app.example.com/auth/callback")
        == "https://app.example.com/auth/callback"
    )


@pytest.mark.parametrize(
    "candidate",
    [
        "https://evil.example/auth/callback",
        "https://app.example.com/other",
        "https://app.example.com/auth/callback?next=https://evil.example",
    ],
)
def test_auth_redirect_rejects_untrusted_destination(candidate: str) -> None:
    settings = Settings(frontend_app_url="https://app.example.com")
    with pytest.raises(AppError, match="redirect"):
        _frontend_callback_url(settings, candidate)
