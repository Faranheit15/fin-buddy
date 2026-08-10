"""Export API endpoints."""

from fastapi import APIRouter, Response

from app.api.deps import CurrentUser, DbSession, OrgContext
from app.services import export_service

router = APIRouter(prefix="/export", tags=["export"])


@router.get("")
async def download_export(
    db: DbSession,
    user: CurrentUser,
    org_ctx: OrgContext,
) -> Response:
    """Download an Excel workbook of core organization data."""
    org, _ = org_ctx

    file_bytes = await export_service.generate_org_export(db, org.id)

    headers = {
        "Content-Disposition": f'attachment; filename="finbuddy_export_{org.slug}.xlsx"',
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    return Response(content=file_bytes, headers=headers)
