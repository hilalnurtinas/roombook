# Architecture

## System overview
Roombook is a room-booking API: users book rooms for time slots, room-owners approve or reject
bookings, and recurring bookings generate a series of occurrences. Built as a single deployable
service (layered architecture) — no module-boundary split, since the domain is small enough that
extra ceremony isn't worth it yet.

## Layers
| Layer | Single responsibility | Owns |
|---|---|---|
| Routers (FastAPI) | HTTP request/response, auth dependency wiring | Route definitions, request/response schemas |
| Services | Business rules (conflict checks, approval, recurrence expansion) | Domain logic, transactions |
| Repositories/Models | Persistence | SQLAlchemy models, queries |

## Communication rules
Routers call services; services call repositories. Routers never touch the DB directly; services
never build HTTP responses.

## Forbidden dependencies (make them testable)
- Routers never import SQLAlchemy models or issue queries directly — only through services.
- Services never import FastAPI request/response types.

## Deliberately out of scope
- Notifications/email, multi-tenant orgs, payment/billing, mobile clients — v1 is the booking API only.
