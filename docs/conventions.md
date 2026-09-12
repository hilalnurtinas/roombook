# Conventions

## Language & framework versions
Python 3.12, FastAPI, SQLAlchemy 2.x (async), Alembic for migrations, PostgreSQL 16, Pydantic v2.

## Naming
- Files/modules/functions/variables: `snake_case`.
- Classes and Pydantic models: `PascalCase`.
- Test files: `test_<module>.py`, mirroring `app/` structure under `tests/`.
- Branches/commits: see `docs/git.md`.

## Error handling
- Domain errors are typed exceptions (e.g. `BookingConflictError`, `NotAuthorizedError`) raised from services.
- A single set of FastAPI exception handlers maps typed exceptions to HTTP responses — routers never catch and translate errors themselves.
- No stack traces or internal exception details ever reach the client; unhandled exceptions become a generic 500.

## Data rules
- Timestamps: UTC, timezone-aware `datetime` everywhere (stored and in transit).
- Primary keys: auto-increment integers.
- Money/percentages: not applicable in v1 (no billing).

## Enforced by tooling
- Formatting/lint: `ruff` (format + check).
- Types: `mypy` in strict-ish mode on `app/`.
- Wire new rules into `scripts/check` whenever possible.
