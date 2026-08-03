"""Shared API schemas."""

from datetime import datetime
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int


class IdResponse(BaseModel):
    id: UUID


class TimestampSchema(ORMModel):
    created_at: datetime
    updated_at: datetime | None = None
