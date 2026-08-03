"""Registered seeders (name, function). Order matters."""

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.seeders.demo_catalog import seed_demo_catalog_metadata

SEEDERS: list[tuple[str, Callable[[Session], None]]] = [
    ("0001_demo_catalog_metadata", seed_demo_catalog_metadata),
]
