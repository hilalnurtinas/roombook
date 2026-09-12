from datetime import UTC, datetime, timedelta

from app.schemas.booking import SuggestedSlot
from app.services.slots import find_free_slots

T0 = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)


def test_no_existing_bookings_returns_nearest_consecutive_slots() -> None:
    slots = find_free_slots(existing=[], requested_start=T0, duration=HOUR)
    assert slots == [
        SuggestedSlot(start_at=T0, end_at=T0 + HOUR),
        SuggestedSlot(start_at=T0 + HOUR, end_at=T0 + 2 * HOUR),
        SuggestedSlot(start_at=T0 + 2 * HOUR, end_at=T0 + 3 * HOUR),
    ]


def test_single_blocking_booking_returns_slot_right_after() -> None:
    existing = [(T0, T0 + HOUR)]
    slots = find_free_slots(existing=existing, requested_start=T0, duration=HOUR)
    assert len(slots) >= 1
    assert slots[0].start_at == T0 + HOUR
    assert slots[0].end_at == T0 + 2 * HOUR


def test_back_to_back_booking_does_not_block_touching_slot() -> None:
    existing = [(T0 + HOUR, T0 + 2 * HOUR)]
    slots = find_free_slots(existing=existing, requested_start=T0, duration=HOUR)
    assert slots[0].start_at == T0
    assert slots[0].end_at == T0 + HOUR


def test_no_gap_in_window_returns_empty_list() -> None:
    existing = [(T0, T0 + timedelta(hours=24))]
    slots = find_free_slots(existing=existing, requested_start=T0, duration=HOUR)
    assert slots == []


def test_returns_up_to_three_gaps_capped() -> None:
    existing = [
        (T0 + HOUR, T0 + 2 * HOUR),
        (T0 + 3 * HOUR, T0 + 4 * HOUR),
        (T0 + 5 * HOUR, T0 + 6 * HOUR),
        (T0 + 7 * HOUR, T0 + 8 * HOUR),
    ]
    slots = find_free_slots(existing=existing, requested_start=T0, duration=HOUR)
    assert len(slots) == 3


def test_ignores_bookings_outside_the_window() -> None:
    existing = [(T0 + timedelta(hours=30), T0 + timedelta(hours=31))]
    slots = find_free_slots(existing=existing, requested_start=T0, duration=HOUR)
    assert slots[0].start_at == T0
