# Domain

## Ubiquitous language
| Term | Meaning | Notes / not to be confused with |
|---|---|---|
| Room | A bookable physical resource (has capacity, location, an owner) | Not a "space" or "resource" in code/specs |
| Booking | A single reservation of one Room for one time range, owned by a User | One occurrence — see Series for recurrence |
| Series | A recurring booking definition (pattern + end date) that generates Bookings (occurrences) | A Series is not itself booked; its occurrences are |
| User | A person who creates bookings | |
| Room-owner | The user responsible for approving/rejecting Bookings on a given Room | Not a global admin — scoped to their own Room(s) |
| Occurrence | One generated Booking belonging to a Series | Each occurrence has its own status |

## Business rules
- BR-1: No two Bookings for the same Room may overlap in time (no double-booking), regardless of status except Rejected/Cancelled.
- BR-2: Every new Booking starts in status `pending`.
- BR-3: Only the owning Room's room-owner may transition a Booking to `confirmed` or `rejected`.
- BR-4: A Series supports `daily` or `weekly` recurrence with a required end date.
- BR-5: Each occurrence of a Series is checked independently for conflicts and approval; a conflicting occurrence is created with status `skipped_conflict` and reported to the requester — it never blocks the rest of the series.
- BR-6: A non-owner User may only view/manage their own Bookings.

## Key domain invariants
- A Booking's time range never overlaps another non-rejected/non-cancelled Booking on the same Room (BR-1) — enforced at the service layer and by a DB constraint.
- A Booking's status is one of: `pending`, `confirmed`, `rejected`, `cancelled`, `skipped_conflict`.
