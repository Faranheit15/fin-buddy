"""API v1 routers."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    cards,
    contacts,
    dashboard,
    health,
    notifications,
    settlements,
    statements,
    transactions,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(cards.router)
api_router.include_router(contacts.router)
api_router.include_router(transactions.router)
api_router.include_router(settlements.router)
api_router.include_router(statements.router)
api_router.include_router(notifications.router)
api_router.include_router(admin.router)
