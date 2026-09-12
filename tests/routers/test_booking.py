from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.models.factories import make_booking, make_room, make_user

T0 = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)


def _payload(room_id: int = 1, start: datetime = T0, end: datetime = T0 + HOUR) -> dict:
    return {
        "room_id": room_id,
        "start_at": start.isoformat(),
        "end_at": end.isoformat(),
    }


async def test_create_booking_succeeds_with_no_conflict(
    client: AsyncClient, test_session: AsyncSession
) -> None:
    await make_user(test_session, id=1, name="Owner")
    await make_room(test_session, id=1, owner_id=1)
    await make_user(test_session, id=2, name="Requester")

    resp = await client.post("/bookings", json=_payload(), headers={"X-User-Id": "2"})

    assert resp.status_code == 201
    body = resp.json()
    assert body["room_id"] == 1
    assert body["user_id"] == 2
    assert body["status"] == "pending"


async def test_conflict_response_lists_conflicting_bookings(
    client: AsyncClient, test_session: AsyncSession
) -> None:
    await make_user(test_session, id=1, name="Owner")
    await make_room(test_session, id=1, owner_id=1)
    await make_user(test_session, id=2, name="Requester")
    await make_booking(test_session, room_id=1, user_id=1, start_at=T0, end_at=T0 + HOUR)

    resp = await client.post("/bookings", json=_payload(), headers={"X-User-Id": "2"})

    assert resp.status_code == 409
    body = resp.json()
    assert len(body["conflicts"]) == 1
    assert datetime.fromisoformat(body["conflicts"][0]["start_at"]) == T0
    assert datetime.fromisoformat(body["conflicts"][0]["end_at"]) == T0 + HOUR


async def test_conflict_response_includes_suggested_slots(
    client: AsyncClient, test_session: AsyncSession
) -> None:
    await make_user(test_session, id=1, name="Owner")
    await make_room(test_session, id=1, owner_id=1)
    await make_user(test_session, id=2, name="Requester")
    await make_booking(test_session, room_id=1, user_id=1, start_at=T0, end_at=T0 + HOUR)

    resp = await client.post("/bookings", json=_payload(), headers={"X-User-Id": "2"})

    assert resp.status_code == 409
    suggestions = resp.json()["suggestions"]
    assert len(suggestions) >= 1
    assert datetime.fromisoformat(suggestions[0]["start_at"]) == T0 + HOUR


async def test_conflict_response_empty_suggestions_when_fully_booked(
    client: AsyncClient, test_session: AsyncSession
) -> None:
    await make_user(test_session, id=1, name="Owner")
    await make_room(test_session, id=1, owner_id=1)
    await make_user(test_session, id=2, name="Requester")
    await make_booking(
        test_session,
        room_id=1,
        user_id=1,
        start_at=T0,
        end_at=T0 + timedelta(hours=24),
    )

    resp = await client.post("/bookings", json=_payload(), headers={"X-User-Id": "2"})

    assert resp.status_code == 409
    assert resp.json()["suggestions"] == []


async def test_end_before_start_rejected(client: AsyncClient, test_session: AsyncSession) -> None:
    await make_user(test_session, id=1, name="Owner")
    await make_room(test_session, id=1, owner_id=1)

    resp = await client.post(
        "/bookings", json=_payload(start=T0, end=T0 - HOUR), headers={"X-User-Id": "1"}
    )

    assert resp.status_code == 422


async def test_missing_required_field_rejected(
    client: AsyncClient, test_session: AsyncSession
) -> None:
    await make_user(test_session, id=1, name="Requester")

    resp = await client.post(
        "/bookings", json={"room_id": 1, "start_at": T0.isoformat()}, headers={"X-User-Id": "1"}
    )

    assert resp.status_code == 422


async def test_missing_current_user_header_rejected(
    client: AsyncClient, test_session: AsyncSession
) -> None:
    await make_user(test_session, id=1, name="Owner")
    await make_room(test_session, id=1, owner_id=1)

    resp = await client.post("/bookings", json=_payload())

    assert resp.status_code == 401


async def test_unresolvable_current_user_rejected(
    client: AsyncClient, test_session: AsyncSession
) -> None:
    await make_user(test_session, id=1, name="Owner")
    await make_room(test_session, id=1, owner_id=1)

    resp = await client.post("/bookings", json=_payload(), headers={"X-User-Id": "999"})

    assert resp.status_code == 401


async def test_unknown_room_rejected(client: AsyncClient, test_session: AsyncSession) -> None:
    await make_user(test_session, id=1, name="Requester")

    resp = await client.post("/bookings", json=_payload(room_id=999), headers={"X-User-Id": "1"})

    assert resp.status_code == 404
