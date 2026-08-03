# Backend Service Context

## Architecture
The backend is a FastAPI service. Code is organized into:
- `app/api`: API route definitions
- `app/core`: Configuration and core logic
- `app/db`: Database connection and session management
- `app/domain`: Core domain entities and logic
- `app/models`: SQLAlchemy ORM models
- `app/schemas`: Pydantic models for validation
- `app/services`: Business logic services
- `tests/`: Pytest test suite

## Coding Style & Naming Conventions
- Python targets 3.12.
- Uses Ruff with a 100-character line length.
- Enforces strict mypy typing.
- Keep modules `snake_case`, classes `PascalCase`, and tests named `test_*.py`.

## Build, Test, and Development Commands
```bash
uv sync --group dev
uv run uvicorn app.main:app --reload --port 8000
```

## Definition of Done (DoD)
Before any backend change is considered complete, you MUST pass all tests and type checks:
```bash
uv run pytest
uv run ruff check .
uv run mypy app
```
