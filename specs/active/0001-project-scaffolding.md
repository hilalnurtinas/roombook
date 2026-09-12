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
- [ ] AC-1 — Running the documented single command starts the app and a Postgres instance; `GET /health` returns HTTP 200 with a body indicating the DB connection succeeded.
- [ ] AC-2 — Stopping/removing the database and re-running the documented migration command recreates the schema from versioned migration files (not from model auto-create).
- [ ] AC-3 — Running the test suite against the real test database passes with 0 failures on an empty test set (harness works, no tests required yet).
- [ ] AC-4 — `ruff check .`, `ruff format --check .`, and `mypy app` each exit 0 on the generated skeleton.
- [ ] AC-5 — Required environment variables are documented in `.env.example`; the app fails fast with a clear error if a required variable is missing (not a silent default or crash trace).
- [ ] AC-6 — `./scripts/check` runs lint, format-check, type-check, and test steps in order and exits 0 on this skeleton.

## Definition of Done
- [ ] Every acceptance criterion mapped to proof (test or reproducible observation)
- [ ] `scripts/check` green
- [ ] Independent review done; real findings fixed, noise rejected with written rationale
- [ ] Docs / ADRs updated if behavior or architecture changed
- [ ] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | |
| Fix rounds | |
| Review findings: real / noise | |
| Regressions introduced | |
| Bugs escaped to production | |

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
