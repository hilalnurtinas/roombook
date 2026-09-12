# Testing

## The contract
- Every acceptance criterion maps to at least one test (criterion ↔ test map lives in the plan).
- Tests assert **behavior**, not implementation details or mere status codes.
- The whole suite runs inside `scripts/check` — one command, everywhere.

## Frameworks & layout
- `pytest` + `pytest-asyncio`. Tests live in `tests/`, mirroring `app/` module structure.
- Integration tests use a real PostgreSQL test database (via a dedicated test DB/container) — never mocked — for anything touching booking-conflict or concurrency logic (BR-1, BR-5).

## What must be tested
- Every business rule in `docs/domain.md` (BR-1 through BR-6), each with at least one direct test.
- Booking overlap detection under concurrent requests (BR-1) — integration test against the real DB.
- Recurrence expansion and per-occurrence conflict handling (BR-4, BR-5).
- Authorization boundaries: room-owner-only approval (BR-3), user-scoped visibility (BR-6).

## Protected-tests rule
Weakening asserts, deleting, or skipping tests to reach green is forbidden. A red test triggers
`prompts/recovery/red-test.md` (R-02) — first decide what is wrong: code, test, or spec.

## Determinism
Flaky tests are fixed, not retried or skipped — see R-03. Evidence of a fix: 5 consecutive green runs.
