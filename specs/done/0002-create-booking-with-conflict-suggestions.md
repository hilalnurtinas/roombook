# Spec 0002 — Create a booking with conflict rejection and nearest-slot suggestions

- Status: Shipped
- Mode: lite (from AGENTS.md at creation time)
- Plan: `specs/plans/0002-plan.md`

## Intent
Roombook currently has no domain models or endpoints — only the app skeleton (spec 0001). The
first real capability users need is the ability to request a room for a time slot. A user wants
to book a specific room for a specific time range and know immediately whether it succeeded; if
the room is already taken for any overlapping part of that range, they want to know exactly which
existing booking(s) conflict and be offered the nearest alternative times on the same room instead
of having to guess-and-retry. Success = a user can create a booking, gets a clear typed rejection
with conflict details and up to three concrete alternative slots when the room isn't free, and no
two non-cancelled/non-rejected bookings on the same room ever overlap.

This spec deliberately does NOT build: authentication/login (a stand-in "current user" resolver is
used instead — real JWT auth is a separate future spec), room/user management endpoints (rooms and
users are minimal persisted records created directly for this spec's tests, not via an API), the
approve/reject workflow for room-owners (BR-3), or recurring bookings/Series (BR-4, BR-5). Those
are out of scope and left to their own specs.

## Requirements
- A user can request to book a specific room for an explicit start and end time.
- The system rejects a booking request that overlaps, in any part, an existing booking on the same
  room that is not itself cancelled or rejected — no two such bookings ever coexist for the same
  room (BR-1).
- A newly created, non-conflicting booking is recorded as pending approval (BR-2); this spec does
  not implement the approval transition itself, only that a booking starts in this state.
- When a booking request is rejected for conflicting, the response tells the requester which
  existing booking(s) it conflicts with (their time range) — not just a generic "conflict" message.
- When a booking request is rejected for conflicting, the response also suggests up to three
  alternative time slots on the same room, of the same requested duration, that do not conflict
  with any existing booking, searched forward in time from the requested start within the next 24
  hours. If no such slot exists in that window, the suggestion list is empty (not an error).
- A user may only request bookings as themselves; the system knows who is requesting a booking
  without a real login system existing yet (a stand-in resolver identifies "the current user" for
  this spec — see Constraints).
- Invalid requests (end time not after start time, missing fields, booking a room that does not
  exist) are rejected with a clear, typed error — never a raw stack trace.

## Constraints & out of scope
- No authentication/login flow. "Current user" is resolved by a stand-in mechanism (e.g. a
  required identifying header consumed by a FastAPI dependency) — good enough to attribute a
  booking to a user, not a security control. Real JWT auth replaces this in a later spec.
- No room-owner approve/reject endpoint or transition (BR-3) — a booking is created and left
  `pending`; nothing in this spec moves it to `confirmed`/`rejected`.
- No recurring bookings / Series / occurrence generation (BR-4, BR-5).
- No room or user management endpoints (create/update/list room, register user). Room and User
  rows needed to exercise this feature are minimal persisted models, created directly (fixtures /
  direct inserts), not through an API.
- No listing/retrieval endpoints for bookings (e.g. "get my bookings") beyond what's needed to
  prove conflict detection — that's a separate spec.
- Slot suggestions only ever consider the same room and the same requested duration; they do not
  suggest a different room or a shorter/longer meeting.
- Slot search window is fixed at 24 hours forward from the requested start time; slots beyond that
  window are never suggested.

## Acceptance criteria
- [x] AC-1 — A booking request for a room with no overlapping existing booking succeeds: the booking is persisted with status `pending`, attributed to the requesting user, and the response echoes room, start, and end time.
- [x] AC-2 — A booking request whose time range fully contains an existing non-cancelled/non-rejected booking on the same room is rejected with a typed conflict error.
- [x] AC-3 — A booking request whose time range partially overlaps (at the start, at the end, or is fully contained within) an existing non-cancelled/non-rejected booking on the same room is rejected with a typed conflict error.
- [x] AC-4 — A booking request whose time range is back-to-back with an existing booking (ends exactly when the existing one starts, or starts exactly when the existing one ends) is accepted — touching boundaries are not treated as overlapping.
- [x] AC-5 — A rejected conflicting request's error response lists the time range(s) of every existing booking it conflicts with.
- [x] AC-6 — A rejected conflicting request's error response includes up to three suggested alternative slots (room, start, end) of the same requested duration, none of which overlap any existing non-cancelled/non-rejected booking on that room, found within 24 hours forward of the requested start.
- [x] AC-7 — When no non-conflicting slot exists on that room within the 24-hour search window, the rejected response's suggestion list is present but empty, not an error.
- [x] AC-8 — A booking request against a room that does not exist is rejected with a typed "not found" error, not a 500 or stack trace.
- [x] AC-9 — A booking request where the end time is not strictly after the start time is rejected with a typed validation error.
- [x] AC-10 — A booking request missing required fields (room, start, or end) is rejected with a typed validation error identifying the missing field(s).
- [x] AC-11 — A booking request with no resolvable current user (missing/invalid identifying header) is rejected with a typed authorization/authentication error, not processed as anonymous.
- [x] AC-12 — A conflict check considers only bookings on the *same* room; an overlapping time range on a *different* room never causes a rejection.
- [x] AC-13 — A conflict check ignores existing bookings on the same room that are `cancelled` or `rejected`; an overlapping request against only such bookings succeeds.
- [x] AC-14 — Two concurrent requests to book the same room for the same overlapping window never both succeed (at most one is persisted as a booking; the other is rejected as a conflict) — proven under real concurrent execution against the database, not sequential calls.

## Verify — criterion ↔ evidence (QA)

Full pass run on branch `feature/0002-create-booking-with-conflicts` @ `cf5edbd`, real Postgres 16
via `docker compose`. `./scripts/check` GREEN (lint, format, types, 31 tests). Also manually
reproduced live against a running app (`uvicorn` + the same Postgres, seeded via direct inserts) —
see the three curl scenarios below re-run for AC-1/AC-4.

| AC | Evidence | Status |
|---|---|---|
| AC-1 | `tests/routers/test_booking.py::test_create_booking_succeeds_with_no_conflict` PASSED (asserts body fields, not just status). Live: `POST /bookings` → `201 {"id":1,"room_id":1,"user_id":2,...,"status":"pending"}`. | Met |
| AC-2 | `tests/services/test_booking_conflict.py::test_full_containment_overlap_rejected` PASSED. | Met |
| AC-3 | `test_partial_start_overlap_rejected`, `test_partial_end_overlap_rejected`, `test_fully_contained_within_existing_rejected` — all PASSED. | Met |
| AC-4 | `test_back_to_back_boundaries_accepted` PASSED. Live: booking starting exactly at prior booking's `end_at` → `201`. DB `EXCLUDE` constraint's `'[)'` range confirmed to match the service query's `<`/`>` operators exactly (independent review). | Met |
| AC-5 | `test_booking.py::test_conflict_response_lists_conflicting_bookings` PASSED (exact range equality, not presence-only). | Met |
| AC-6 | `test_conflict_response_includes_suggested_slots` + `test_slots.py::test_returns_up_to_three_gaps_capped` PASSED. Live: 409 body included 3 correct suggested slots. | Met |
| AC-7 | `test_conflict_response_empty_suggestions_when_fully_booked` PASSED (real 24h-spanning booking, not a stub) + `test_slots.py::test_no_gap_in_window_returns_empty_list`. | Met |
| AC-8 | `test_booking_conflict.py::test_unknown_room_raises_not_found` (service) + `test_booking.py::test_unknown_room_rejected` (HTTP 404) — both PASSED. | Met |
| AC-9 | `test_end_before_start_rejected` (end < start) + `test_end_at_equal_to_start_at_rejected` (end == start, added in QA fix round) — both PASSED, both asserting the validation message. | Met |
| AC-10 | `test_missing_required_field_rejected` PASSED — asserts `("body","end_at")` appears in the error `loc` (fixed in review round 1; was status-code-only before). | Met |
| AC-11 | `test_missing_current_user_header_rejected` (no header → 401), `test_unresolvable_current_user_rejected` (unknown id → 401), `test_non_integer_user_id_header_rejected` (malformed id → 422, added in QA fix round) — all PASSED. See "Accepted follow-up" note below on the 422-vs-401 nuance for the malformed-header sub-case. | Met (with a documented, non-blocking nuance) |
| AC-12 | `test_overlap_on_different_room_not_a_conflict` PASSED. | Met |
| AC-13 | `test_cancelled_and_rejected_bookings_ignored` PASSED. | Met |
| AC-14 | `test_booking_concurrency.py::test_concurrent_overlapping_requests_only_one_succeeds` PASSED, using two independent live DB connections (not the shared rolled-back-transaction fixture) — re-run 5x consecutively with no flakiness during build; independently confirmed by review to exercise the DB exclusion constraint itself, not app-level serialization. | Met |

**Accepted follow-up / open decision (non-blocking):** AC-11's wording ("invalid identifying
header ... typed authorization/authentication error") is satisfied for a *missing* header or a
*well-formed-but-unresolvable* user id (both → `401 UnresolvedUserError`). A *malformed* header
(e.g. `X-User-Id: not-a-number`) instead surfaces as FastAPI's own `422` type-coercion error,
because header parsing happens before `app.auth.get_current_user` runs. This is still a typed,
non-500 rejection — the request is never treated as anonymous — so it is not a spec violation, but
it is a different status code than the other two sub-cases of the same criterion. Decision: accept
as-is for v1 (documented in `tests/routers/test_booking.py::test_non_integer_user_id_header_rejected`);
revisit only if/when real auth replaces the `X-User-Id` stand-in, since that rework will replace
this code path anyway.

## Definition of Done
- [x] Every acceptance criterion mapped to proof (test or reproducible observation)
- [x] `scripts/check` green
- [x] Independent review done; real findings fixed, noise rejected with written rationale
- [x] Docs / ADRs updated if behavior or architecture changed (README's "API" section documents `POST /bookings` and the `X-User-Id` stand-in; no ADR needed — no architectural decision beyond what's recorded in this spec/plan)
- [x] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | 0 (clarifying questions resolved before first draft; no revisions after) |
| Fix rounds | 2 (review round 1: AC-10 test-assertion fix; QA-verify round: AC-9/AC-11 boundary test additions) |
| Review findings: real / noise | 1 real (AC-10 status-code-only test) / 1 noise (unconditional 24h-window query — accepted as informational, no action) |
| Regressions introduced | 0 |
| Bugs escaped to production | 0 |

## Review round 1 — triage
Independent review (fresh reviewer subagent, read-only) ran `./scripts/check` and inspected the
diff against this spec and `specs/plans/0002-plan.md`, including live SQL introspection of the
exclusion constraint. Verdict: clean except two findings.
- **Real — fixed.** `tests/routers/test_booking.py::test_missing_required_field_rejected` asserted
  only the `422` status code, not that the response body identifies `end_at` by name (AC-10
  requires field identification). Fixed by asserting `("body","end_at")` appears in the error
  `loc` list.
- **Noise — accepted, no action.** `app/services/booking.py` unconditionally fetches the full 24h
  window of active bookings on every request, even conflict-free ones, though only the exact
  overlap range is needed for the happy path. Not a real problem at v1 scale (plan's Risks section
  already accepted this trade-off); flagged as informational only.

## QA verify round — gaps found and closed
QA verify (meaning-check, not just green tests) found two acceptance criteria with a tested case
but an untested boundary, both already behaving correctly in production code:
- **AC-9** — only `end_at < start_at` was tested; `end_at == start_at` was untested. Added
  `test_end_at_equal_to_start_at_rejected`.
- **AC-11** — a malformed (non-integer) `X-User-Id` was untested. Added
  `test_non_integer_user_id_header_rejected`, documenting the accepted 422-vs-401 nuance recorded
  above.

Both closed with test-only changes (`cf5edbd`) — no production code modified, no behavior changed.

## Self-critique (hostile-reader pass)

Gaps a developer would still ask about, each with a recommendation — folded into the sections
above where a decision was needed; listed here for visibility since this is the first domain spec
and sets precedent:

1. **What identifies "the current user" mechanically?** Recommendation (folded into Constraints):
   a required header, e.g. `X-User-Id`, resolved via a FastAPI dependency into a `User` row that
   must exist; missing/unresolvable → AC-11's typed error. Exact header name is a plan-level
   ("how") decision, not a spec-level one — left to the plan.
2. **Should the requester be allowed to book on behalf of someone else / any room, or only rooms
   they have some relationship to?** Recommendation: no ownership restriction on *who may request*
   a booking on a room in v1 (BR-6 restricts *viewing/managing your own bookings*, not who may
   request one) — any resolved user may request any existing room. Folded in as the default;
   flagging because domain.md doesn't say this explicitly.
3. **Does "up to three slots" search only within the same day, or can it cross midnight into the
   next day?** Recommendation (folded into Requirements): pure 24-hour rolling window from the
   requested start, no day-boundary special-casing — simplest rule, matches the approved clarify
   answer.
4. **What happens if the requested duration is longer than 24 hours?** No slot could ever be
   suggested within the 24h window in that case. Recommendation: acceptable — AC-7 already covers
   "no slot found → empty list, not an error"; no separate rule needed. Not folding in a special
   case, flagging so it isn't mistaken for an oversight.
5. **Is there a minimum/maximum booking duration?** Recommendation: not constrained in this spec
   (any `end > start` is valid per AC-9) — domain.md defines no such rule, and inventing one would
   be a technical/business decision beyond this spec's scope. If a real minimum is wanted, it's a
   follow-up spec decision.

## Decisions (resolved clarifying questions — approved by human)
1. **Auth scope:** stub current-user resolution (no real login); real JWT auth is a separate spec.
2. **Request shape:** explicit `start_at` / `end_at` (UTC, timezone-aware), not start+duration.
3. **Slot suggestion rule:** up to 3 slots, same room, same requested duration, searched forward
   within a 24-hour window from the requested start; empty list (not an error) if none found.
4. **Room/User prerequisite:** minimal `Room` and `User` persistence only, created directly for
   this spec's tests — no create-room/register-user endpoints in this spec.
