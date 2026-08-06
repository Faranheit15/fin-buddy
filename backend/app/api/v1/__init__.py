"""API v1 routers."""

from fastapi import APIRouter

from app.api.v1 import (
    accounts,
    admin,
    auth,
    cards,
    categories,
    contacts,
    dashboard,
    emis,
    export,
    health,
    jobs,
    notifications,
    obligations,
    settlements,
    statements,
    transactions,
    transfers,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(accounts.router)
api_router.include_router(cards.router)
api_router.include_router(contacts.router)
api_router.include_router(transactions.router)
api_router.include_router(obligations.router)
api_router.include_router(settlements.router)
api_router.include_router(statements.router)
api_router.include_router(notifications.router)
api_router.include_router(admin.router)
api_router.include_router(categories.router)
api_router.include_router(transfers.router)
api_router.include_router(emis.router)
api_router.include_router(export.router)
api_router.include_router(jobs.router)
