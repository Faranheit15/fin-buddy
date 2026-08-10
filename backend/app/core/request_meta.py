"""Trusted request metadata helpers shared by logging and rate limiting."""

from __future__ import annotations

import uuid
from urllib.parse import parse_qsl, urlencode

from starlette.requests import Request

from app.core.config import Settings, get_settings

MAX_REQUEST_ID_LENGTH = 128
MAX_LOGGED_QUERY_PARAMETERS = 50


def request_id(request: Request) -> str:
    """Return a bounded, header-safe correlation ID for a request."""
    candidate = request.headers.get("x-request-id", "").strip()
    if (
        candidate
        and len(candidate) <= MAX_REQUEST_ID_LENGTH
        and candidate.isascii()
        and candidate.isprintable()
    ):
        return candidate
    return str(uuid.uuid4())


def client_ip(request: Request, settings: Settings | None = None) -> str | None:
    """Return a client address, trusting forwarding headers only from configured proxies."""
    peer_ip = request.client.host if request.client else None
    cfg = settings or get_settings()
    if not peer_ip or peer_ip not in cfg.trusted_proxy_ips:
        return peer_ip

    forwarded = request.headers.get("x-forwarded-for")
    if not forwarded:
        return peer_ip
    candidate = forwarded.split(",", maxsplit=1)[0].strip()
    return candidate or peer_ip


def redacted_query_string(request: Request) -> str | None:
    """Return query parameter names without retaining their potentially sensitive values."""
    query = request.url.query
    if not query:
        return None

    parameters = parse_qsl(query, keep_blank_values=True)
    redacted = [(key, "[REDACTED]") for key, _ in parameters[:MAX_LOGGED_QUERY_PARAMETERS]]
    if len(parameters) > MAX_LOGGED_QUERY_PARAMETERS:
        redacted.append(("_truncated", "[REDACTED]"))
    return urlencode(redacted)
