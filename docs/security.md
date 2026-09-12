# Security

## Secrets
- Secrets never enter the repo, specs, prompts, or chat. `.env` is gitignored; provide `.env.example`.
- Agents never print secret values, even when debugging.

## Input & output
- All request bodies validated via Pydantic schemas at the router boundary.
- Errors returned to clients are generic, typed error responses (see `docs/conventions.md`) — never raw exception text or stack traces.

## AuthN / AuthZ
- AuthN: JWT access tokens issued on login; passwords hashed with bcrypt/argon2, never stored or logged in plaintext.
- AuthZ: role/ownership checks enforced via FastAPI dependencies at the route level — `User` (own bookings only) vs room-owner (approve/reject on owned rooms only).
- Default-deny: every route requires a valid token unless explicitly marked public (login, health check).

## Dependencies
- New dependencies require a one-line justification in the PR description; avoid unmaintained or single-maintainer packages for anything security-sensitive (auth, crypto).

## Review lens
Security is a mandatory dimension of every independent review (see `prompts/review.md`), not a
separate afterthought phase.
