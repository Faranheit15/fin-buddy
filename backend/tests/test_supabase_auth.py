"""Unit tests for SupabaseAuthClient headers and key handling."""

from app.core.config import Settings
from app.infrastructure.supabase_auth import SupabaseAuthClient


def test_headers_opaque_publishable_key() -> None:
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_anon_key="sb_publishable_abcdef1234567890",
    )
    client = SupabaseAuthClient(settings)
    headers = client._headers()
    assert headers["apikey"] == "sb_publishable_abcdef1234567890"
    assert headers["Content-Type"] == "application/json"
    # Opaque keys must NEVER be sent as Authorization: Bearer
    assert "Authorization" not in headers


def test_headers_opaque_secret_key_service_mode() -> None:
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_anon_key="sb_publishable_abcdef1234567890",
        supabase_service_role_key="sb_secret_secret1234567890",
    )
    client = SupabaseAuthClient(settings)
    headers = client._headers(service=True)
    assert headers["apikey"] == "sb_secret_secret1234567890"
    assert "Authorization" not in headers


def test_headers_opaque_key_with_user_access_token() -> None:
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_anon_key="sb_publishable_abcdef1234567890",
    )
    client = SupabaseAuthClient(settings)
    user_token = "user_session_access_token_123"
    headers = client._headers(access_token=user_token)
    assert headers["apikey"] == "sb_publishable_abcdef1234567890"
    # Authorization header is populated ONLY for user session access tokens
    assert headers["Authorization"] == f"Bearer {user_token}"


def test_headers_legacy_jwt_key() -> None:
    legacy_anon = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiJ9.fake_signature"
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_anon_key=legacy_anon,
    )
    client = SupabaseAuthClient(settings)
    headers = client._headers()
    assert headers["apikey"] == legacy_anon
    assert headers["Authorization"] == f"Bearer {legacy_anon}"


def test_headers_with_supabase_publishable_key_setting() -> None:
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_publishable_key="sb_publishable_modern123456",
    )
    client = SupabaseAuthClient(settings)
    headers = client._headers()
    assert headers["apikey"] == "sb_publishable_modern123456"
    assert "Authorization" not in headers
