# Spec 0001 — Project scaffolding

- Status: Approved
- Mode: lite (from AGENTS.md at creation time)
- Plan: `specs/plans/0001-plan.md`

## Intent
Roombook has no runnable code yet — only workspace docs/rules (see `docs/architecture.md`,
`docs/conventions.md`). Before any domain feature (rooms, bookings, approval, recurrence) can be
built, we need a working FastAPI application skeleton: installable dependencies, a database
connection, migrations, config/secrets handling, and a test harness — so that `scripts/check`
actually runs something and the first feature spec can add real endpoints instead of also
inventing the app's plumbing. Success = a `GET /health` endpoint returns 200 from a running app,
backed by a real Postgres connection, with lint/type/test tooling green in CI-equivalent form.
No domain logic (rooms, bookings, auth) is added in this spec — that's out of scope.

## Requirements
- A running HTTP application exposes a health-check endpoint confirming the app is up and can
  reach its database.
- The application's configuration (DB connection, secrets) is supplied via environment variables,
  never hardcoded, with a documented example of what's required to run it.
- The database schema is managed through versioned migrations, not created ad hoc.
- A test suite can run against a real, isolated test database, and passes with zero tests failing
  when there are no tests yet (an empty/no-op suite is not an error).
- Linting and type-checking run over the codebase and pass on the empty skeleton.
- A developer can start the whole stack (app + database) with a single documented command.

## Constraints & out of scope
- No Room, Booking, Series, or User domain models/endpoints — scaffolding only.
- No authentication/authorization implementation (JWT, roles) — stubbed out at most as a TODO,
  not built.
- No production deployment concerns (hosting, CI/CD pipeline config) beyond what's needed to run
  `scripts/check` locally.
- No admin UI, notifications, or non-API clients.

## Acceptance criteria
- [x] AC-1 — Running the documented single command starts the app and a Postgres instance; `GET /health` returns HTTP 200 with a body indicating the DB connection succeeded.
- [x] AC-2 — Stopping/removing the database and re-running the documented migration command recreates the schema from versioned migration files (not from model auto-create).
- [x] AC-3 — Running the test suite against the real test database passes with 0 failures on an empty test set (harness works, no tests required yet).
- [x] AC-4 — `ruff check .`, `ruff format --check .`, and `mypy app` each exit 0 on the generated skeleton.
- [x] AC-5 — Required environment variables are documented in `.env.example`; the app fails fast with a clear error if a required variable is missing (not a silent default or crash trace).
- [x] AC-6 — `./scripts/check` runs lint, format-check, type-check, and test steps in order and exits 0 on this skeleton.

## Verify — criterion ↔ evidence (QA)

Re-run live against branch `feature/0001-project-scaffolding` @ commit `ace0093` + the fix-round-2
`.env`-loading patch, in a genuinely clean shell (`env -i PATH="$PATH" HOME="$HOME" sh -c ...`, no
pre-exported DB vars) with a real Postgres 16 via `docker compose`.

| Acceptance criterion | Evidence | Status |
|---|---|---|
| AC-1 | `docker compose up -d --build app` (fresh build) → `curl http://localhost:8000/health` → `HTTP 200`, body `{"status":"ok","database":"connected"}`. Negative path also proven: `docker compose stop db` → same request → `HTTP 503`, `{"status":"error","database":"unreachable"}`. Automated: `tests/routers/test_health.py::test_health_returns_ok_and_connected` and `::test_health_returns_503_when_database_unreachable`, both PASSED. | Met |
| AC-2 | `docker compose exec app alembic upgrade head` on a fresh `roombook` DB → log shows `Running upgrade -> 0001, initial marker migration`; `SELECT * FROM alembic_version` → `0001`. `alembic downgrade base` → log shows `Running downgrade 0001 ->`; `\dt` afterward shows only `alembic_version` remains (no domain tables, per M7's accepted scope). Plumbing-level proof only, as scoped by M7. | Met (scoped) |
| AC-3 | `pytest -v` against `roombook_test` (real container, not mocked): `3 passed in 0.04s` — `test_health_returns_ok_and_connected`, `test_health_returns_503_when_database_unreachable`, `test_missing_required_env_var_fails_fast`. Each test would fail if the behavior broke: the 200/503 tests assert on both status code and body content (not just status), and the transaction-rollback fixture (`tests/conftest.py`) was itself exercised by fix-round-1's M6 change. | Met |
| AC-4 | `./scripts/check` steps `lint`/`format`/`types`: `ruff check .` → "All checks passed!"; `ruff format --check .` → "93 files already formatted"; `mypy app` → "Success: no issues found in 9 source files". All exit 0. | Met |
| AC-5 | `.env.example` documents `DATABASE_URL`, `TEST_DATABASE_URL`, `DB_HOST_PORT`. Fail-fast reproduced live: unsetting a required var and running the app prints `roombook: missing required environment variable(s): database_url` and exits 1 (no stack trace). Covered by `tests/test_config.py::test_missing_required_env_var_fails_fast`, PASSED. | Met |
| AC-6 | `env -i PATH="$PATH" HOME="$HOME" sh -c './scripts/check'` (clean shell, no pre-exported env) → `lint`, `format`, `types`, `test` all ran in order, `CHECK GREEN (4 steps)`. This re-run is also the regression check for fix-round-2's `.env`-loading fix — it was this exact command that reproduced the M4-introduced `KeyError` before the fix, and it is green after. | Met |

**Gaps / caveats, stated explicitly (not hidden):**
- AC-2's evidence is plumbing-only (empty marker migration), by design — see spec's M7 note. It
  does not prove a real schema gets created from migrations, because this spec has no schema yet.
  That gap is intentionally deferred to the first domain-model spec, not silently dropped.
- No test in this skeleton asserts against a real `Room`/`Booking`/`User` row, since none exist —
  `tests/routers/test_health.py` and `tests/test_config.py` are the only tests, and both assert
  observable behavior (HTTP status + body, or process exit code + stderr message), not
  implementation details.

## Definition of Done
- [x] Every acceptance criterion mapped to proof (test or reproducible observation)
- [x] `scripts/check` green
- [x] Independent review done; real findings fixed, noise rejected with written rationale
- [x] Docs / ADRs updated if behavior or architecture changed (no architecture/decision changes beyond what's recorded in this spec)
- [x] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | 2 (review round 1 addendum; fix round 2 + verify table addendum) |
| Fix rounds | 2 (ace0093: M1-M6, L1/L4/L6/L7/L9; 4499d08: M4-introduced regression) |
| Review findings: real / noise | 16 real (6 M-findings + 5 L-findings fixed + 4 L-findings deferred-but-real + 1 regression found in narrow re-review) / 1 noise (M7, accepted as scaffolding-scope limitation, not a defect) |
| Regressions introduced | 1 (fix round 1's M4 change broke the local `./scripts/check` test path by dropping the only thing that loaded `.env` for `TEST_DATABASE_URL`; caught by narrow re-review before merge, fixed in fix round 2) |
| Bugs escaped to production | 0 (caught pre-merge) |

## Decisions (resolved self-critique — approved by human)
1. Postgres 16, run via `docker-compose.yml` (app + db services).
2. App layout: `app/routers`, `app/services`, `app/models`, `app/db.py`, `app/config.py`.
3. Test isolation: separate `roombook_test` database on the same Postgres container.
4. Config via `pydantic-settings`, fail-fast on missing required env vars.
5. Migrations via Alembic.

## Review round 1 — triage
Independent review (fresh reviewer subagent) ran `./scripts/check`, `docker compose`, and manual
reproductions against the built code. Findings M1–M6 accepted as real and fixed (test tautology,
missing service layer, crash-trace fail-fast, test config leaking into prod settings, no
DB-down handling, no test-transaction isolation). L1, L4, L6, L7, L9 fixed as cheap now.
L2, L3, L5, L8 deferred (recorded, not blocking).

- **M7 — accepted scaffolding limitation, not a defect.** AC-2 says migrations "recreate the
  schema"; this spec adds zero domain models, so the one migration (`0001_initial`) is
  intentionally an empty marker (`upgrade()`/`downgrade()` are no-ops) — the plan authorized this.
  Proof for AC-2 in this spec is at the plumbing level only: `alembic upgrade head` against a
  fresh database creates the `alembic_version` table and stamps `0001`; `alembic downgrade base`
  reverses it. The first feature spec that adds a real model will exercise a real schema-bearing
  migration and re-prove AC-2 at that level.

## Fix round 2 — narrow re-review of ace0093

Independent narrow re-review (fresh reviewer subagent, read-only) verified each of M1-M6, L1, L4,
L6, L7, L9 against the actual diff and by running `./scripts/check`, `pytest`, and
`docker compose` live. All ten held up under direct verification — except one regression the fix
itself introduced:

- **Real finding — M4's fix broke the documented local test workflow.** Dropping
  `test_database_url` from `Settings` meant `tests/conftest.py` read `TEST_DATABASE_URL` straight
  from `os.environ`, with nothing loading `.env` into the process first (the declared
  `python-dotenv` dependency was never actually invoked). Reproduced live: following
  `README.md`'s documented steps (`cp .env.example .env`, fill in values, `./scripts/check` from a
  shell with no exported env vars) failed at the test step with
  `KeyError: 'TEST_DATABASE_URL'`.
- **Fix applied:** `tests/conftest.py` now calls `load_dotenv()` before reading
  `TEST_DATABASE_URL`, matching how `app/config.py` already sources `.env` for the app itself.
  Re-verified by running `env -i PATH="$PATH" HOME="$HOME" sh -c './scripts/check'` (a genuinely
  clean shell, no pre-exported DB vars) end to end: lint, format, types, and all 3 tests green.
