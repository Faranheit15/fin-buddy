"""Supabase Auth (GoTrue) HTTP client."""

from typing import Any
from uuid import UUID

import httpx

from app.core.config import Settings
from app.core.exceptions import AppError, UnauthorizedError


class SupabaseAuthClient:
    """Thin wrapper around Supabase Auth REST API."""

    def __init__(self, settings: Settings) -> None:
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise AppError(
                "Supabase Auth is not configured",
                code="auth_not_configured",
                status_code=503,
            )
        self._base = settings.supabase_url.rstrip("/") + "/auth/v1"
        self._anon_key = settings.supabase_anon_key
        self._service_key = settings.supabase_service_role_key
        self._timeout = httpx.Timeout(30.0)

    def _headers(self, *, access_token: str | None = None, service: bool = False) -> dict[str, str]:
        key = self._service_key if service and self._service_key else self._anon_key
        headers = {
            "apikey": key,
            "Content-Type": "application/json",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        elif service and self._service_key:
            headers["Authorization"] = f"Bearer {self._service_key}"
        else:
            headers["Authorization"] = f"Bearer {self._anon_key}"
        return headers

    async def sign_up_email(
        self,
        email: str,
        password: str,
        *,
        data: dict[str, Any] | None = None,
        email_redirect_to: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"email": email, "password": password}
        options: dict[str, Any] = {}
        if data:
            options["data"] = data
        if email_redirect_to:
            options["email_redirect_to"] = email_redirect_to
        if options:
            payload["options"] = options
        return await self._post("/signup", payload)

    async def sign_in_email(self, email: str, password: str) -> dict[str, Any]:
        return await self._post(
            "/token?grant_type=password",
            {"email": email, "password": password},
        )

    async def sign_in_magic_link(self, email: str, *, redirect_to: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"email": email}
        if redirect_to:
            payload["options"] = {"email_redirect_to": redirect_to}
        # OTP endpoint for magic link / email OTP
        return await self._post("/otp", {**payload, "create_user": True})

    async def send_phone_otp(self, phone: str) -> dict[str, Any]:
        return await self._post("/otp", {"phone": phone, "create_user": True})

    async def verify_otp(
        self,
        *,
        email: str | None = None,
        phone: str | None = None,
        token: str,
        type: str = "email",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"token": token, "type": type}
        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        return await self._post("/verify", payload)

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        return await self._post(
            "/token?grant_type=refresh_token",
            {"refresh_token": refresh_token},
        )

    async def logout(self, access_token: str) -> None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base}/logout",
                headers=self._headers(access_token=access_token),
            )
            if response.status_code >= 400:
                # Logout is best-effort
                return

    async def get_user(self, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base}/user",
                headers=self._headers(access_token=access_token),
            )
            if response.status_code == 401:
                raise UnauthorizedError("Invalid or expired access token")
            if response.status_code >= 400:
                raise AppError(
                    f"Supabase get_user failed: {response.text}",
                    code="supabase_error",
                    status_code=502,
                )
            data: dict[str, Any] = response.json()
            return data

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base}{path}",
                headers=self._headers(),
                json=payload,
            )
            data: dict[str, Any]
            try:
                data = response.json()
            except Exception:
                data = {"message": response.text}

            if response.status_code >= 400:
                msg = data.get("error_description") or data.get("msg") or data.get("message") or response.text
                code = data.get("error_code") or data.get("error") or "supabase_auth_error"
                status = 401 if response.status_code in (401, 403) else 400
                if response.status_code >= 500:
                    status = 502
                raise AppError(str(msg), code=str(code), status_code=status, details=data)
            return data


def extract_user_id(auth_response: dict[str, Any]) -> UUID:
    user = auth_response.get("user") or auth_response
    user_id = user.get("id")
    if not user_id:
        raise AppError("Auth response missing user id", code="auth_response_invalid", status_code=502)
    return UUID(str(user_id))
