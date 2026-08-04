"""Auth request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import OrgRole, PlatformRole
from app.schemas.common import ORMModel


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=200)
    redirect_to: str | None = Field(
        default=None,
        description="Frontend callback URL for email confirmation links",
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class MagicLinkRequest(BaseModel):
    email: EmailStr
    redirect_to: str | None = None


class PhoneOtpRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return value.strip()


class VerifyOtpRequest(BaseModel):
    token: str = Field(min_length=4, max_length=64)
    email: EmailStr | None = None
    phone: str | None = None
    type: str = Field(
        default="email",
        description="email | sms | magiclink | recovery | invite | ...",
    )


class RefreshRequest(BaseModel):
    refresh_token: str


class SessionFromTokensRequest(BaseModel):
    """Establish app session from tokens (e.g. after OAuth redirect)."""

    access_token: str = Field(min_length=20)
    refresh_token: str | None = None
    expires_in: int | None = None
    expires_at: int | None = None


class TokenPair(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    expires_in: int | None = None
    expires_at: int | None = None
    token_type: str = "bearer"


class ProfileResponse(ORMModel):
    id: UUID
    email: str | None
    phone: str | None
    display_name: str | None
    avatar_url: str | None
    timezone: str
    due_soon_days: int = 7
    high_utilization_percent: int = 80
    platform_role: PlatformRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime


class ProfileUpdate(BaseModel):
    """User-editable profile + in-app notification thresholds."""

    display_name: str | None = Field(default=None, max_length=200)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    due_soon_days: int | None = Field(default=None, ge=1, le=30)
    high_utilization_percent: int | None = Field(default=None, ge=50, le=100)


class OrganizationSummary(ORMModel):
    id: UUID
    name: str
    slug: str
    role: OrgRole


class OrganizationUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class AuthResponse(BaseModel):
    user: ProfileResponse | None = None
    organization: OrganizationSummary | None = None
    session: TokenPair | None = None
    message: str | None = None
    raw: dict[str, object] | None = None


class GoogleOAuthResponse(BaseModel):
    url: str
    note: str = (
        "Open this URL in the browser. After Google consent, Supabase redirects "
        "to your redirect_to. The frontend should post returned tokens to "
        "POST /api/v1/auth/session so the backend establishes the app profile."
    )


class MeResponse(BaseModel):
    user: ProfileResponse
    organizations: list[OrganizationSummary]
