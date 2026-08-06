"""Email sending service via Resend."""

import httpx
import structlog

from app.core.config import Settings

logger = structlog.get_logger(__name__)


async def send_email(
    settings: Settings,
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    """Send an email using Resend API."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not configured, skipping email", to=to_email, subject=subject)
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            # Use a verified domain in production
            "from": "Fin Buddy <noreply@finbuddy.local>",
            "to": [to_email],
            "subject": subject,
            "text": text_body,
        }
        if html_body:
            payload["html"] = html_body

        res = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json=payload,
        )
        if res.status_code >= 400:
            logger.error("Failed to send email via Resend", status=res.status_code, text=res.text)
