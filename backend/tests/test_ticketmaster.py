from datetime import datetime, timezone
from typing import Any

import pytest
import requests
from events.ingestion.pipeline import EventIngestionPipeline
from events.models import Event, EventFormat, EventSourceRecord
from events.providers.ticketmaster import (
    TicketmasterProvider,
    TicketmasterProviderError,
)

NOW = datetime(2026, 10, 2, 18, tzinfo=timezone.utc)


class FakeResponse:
    def __init__(
        self,
        payload: Any,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.payload = payload
        self.status_code = status_code
        self.headers = headers or {}

    def json(self) -> Any:
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeSession:
    def __init__(self, responses: list[FakeResponse | Exception]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, **kwargs) -> FakeResponse:
        self.calls.append({"url": url, **kwargs})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def ticketmaster_event(**overrides) -> dict[str, Any]:
    event = {
        "id": "tm-123",
        "name": "Utah Jazz Live",
        "url": "https://www.ticketmaster.com/event/tm-123",
        "info": "An evening performance.",
        "pleaseNote": "Doors open at 6.",
        "dates": {
            "start": {
                "dateTime": "2026-10-10T01:00:00Z",
                "localDate": "2026-10-09",
                "localTime": "19:00:00",
            },
            "end": {"dateTime": "2026-10-10T04:00:00Z"},
            "timezone": "America/Denver",
        },
        "promoter": {"name": "Live Nation"},
        "classifications": [
            {
                "segment": {"name": "Music"},
                "genre": {"name": "Jazz"},
                "subGenre": {"name": "Undefined"},
            }
        ],
        "_embedded": {
            "venues": [
                {
                    "name": "Delta Center",
                    "timezone": "America/Denver",
                    "address": {"line1": "301 S Temple", "line2": "Suite 1"},
                    "city": {"name": "Salt Lake City"},
                    "state": {"name": "Utah", "stateCode": "UT"},
                    "country": {"name": "United States", "countryCode": "US"},
                    "location": {"latitude": "40.7683", "longitude": "-111.9011"},
                }
            ]
        },
    }
    event.update(overrides)
    return event


def page(events: list[Any], *, number: int = 0, total_pages: int = 1) -> dict[str, Any]:
    return {
        "_embedded": {"events": events},
        "page": {
            "size": 100,
            "totalElements": len(events),
            "totalPages": total_pages,
            "number": number,
        },
    }


def provider(
    responses: list[FakeResponse | Exception],
    **overrides,
) -> tuple[TicketmasterProvider, FakeSession]:
    session = FakeSession(responses)
    values = {
        "api_key": "test-secret",
        "latitude": 40.2338,
        "longitude": -111.6585,
        "radius_miles": 50.0,
        "days": 90,
        "session": session,
        "request_interval": 0,
        "sleeper": lambda _seconds: None,
        "now": NOW,
    }
    values.update(overrides)
    return TicketmasterProvider(**values), session


def test_successful_response_maps_ticketmaster_event_to_raw_event() -> None:
    adapter, session = provider([FakeResponse(page([ticketmaster_event()]))])

    events = adapter.fetch_events()

    assert len(events) == 1
    event = events[0]
    assert event.external_id == "tm-123"
    assert event.title == "Utah Jazz Live"
    assert event.description == "An evening performance.\n\nDoors open at 6."
    assert event.start_time.isoformat() == "2026-10-10T01:00:00+00:00"
    assert event.end_time.isoformat() == "2026-10-10T04:00:00+00:00"
    assert event.timezone == "America/Denver"
    assert event.organizer_name == "Live Nation"
    assert event.venue_name == "Delta Center"
    assert event.address == "301 S Temple, Suite 1"
    assert event.city == "Salt Lake City"
    assert event.state_region == "UT"
    assert event.country == "US"
    assert event.latitude == pytest.approx(40.7683)
    assert event.longitude == pytest.approx(-111.9011)
    assert event.format_hint == EventFormat.IN_PERSON
    assert event.source_categories == ["Music", "Jazz"]
    assert event.raw_data["id"] == "tm-123"
    assert "apikey" not in event.raw_data

    params = session.calls[0]["params"]
    assert params["geoPoint"]
    assert "latlong" not in params
    assert params["radius"] == 50
    assert isinstance(params["radius"], int)
    assert params["unit"] == "miles"
    assert params["countryCode"] == "US"
    assert params["startDateTime"] == "2026-10-02T18:00:00Z"
    assert params["endDateTime"] == "2026-12-31T18:00:00Z"
    assert params["sort"] == "date,asc"


def test_missing_optional_ticketmaster_fields_are_safe() -> None:
    record = ticketmaster_event(
        info=None,
        pleaseNote=None,
        promoter=None,
        classifications=None,
        _embedded={},
        dates={
            "start": {
                "localDate": "2026-10-09",
                "localTime": "19:00:00",
            },
            "timezone": "America/Denver",
        },
    )
    adapter, _session = provider([FakeResponse(page([record]))])

    event = adapter.fetch_events()[0]

    assert event.description == ""
    assert event.end_time is None
    assert event.venue_name == ""
    assert event.latitude is None
    assert event.longitude is None
    assert event.format_hint == EventFormat.OTHER
    assert event.start_time.utcoffset().total_seconds() == -6 * 60 * 60


def test_pagination_fetches_all_available_pages() -> None:
    adapter, session = provider(
        [
            FakeResponse(page([ticketmaster_event(id="one")], number=0, total_pages=2)),
            FakeResponse(page([ticketmaster_event(id="two")], number=1, total_pages=2)),
        ]
    )

    events = adapter.fetch_events()

    assert [event.external_id for event in events] == ["one", "two"]
    assert adapter.pages_fetched == 2
    assert [call["params"]["page"] for call in session.calls] == [0, 1]


def test_max_pages_stops_pagination() -> None:
    adapter, session = provider(
        [FakeResponse(page([ticketmaster_event()], number=0, total_pages=20))],
        max_pages=1,
    )

    assert len(adapter.fetch_events()) == 1
    assert len(session.calls) == 1


def test_response_without_embedded_events_is_empty() -> None:
    adapter, _session = provider([FakeResponse({"page": {"totalPages": 0}})])

    assert adapter.fetch_events() == []
    assert adapter.records_retrieved == 0


def test_unauthorized_response_raises_sanitized_error_without_retry() -> None:
    adapter, session = provider([FakeResponse({}, status_code=401)])

    with pytest.raises(TicketmasterProviderError) as exc_info:
        adapter.fetch_events()

    assert "credentials" in str(exc_info.value)
    assert "test-secret" not in str(exc_info.value)
    assert len(session.calls) == 1


def test_rate_limit_response_retries_then_succeeds() -> None:
    adapter, session = provider(
        [
            FakeResponse({}, status_code=429, headers={"Retry-After": "0"}),
            FakeResponse(page([])),
        ]
    )

    assert adapter.fetch_events() == []
    assert len(session.calls) == 2


def test_transient_server_error_retries_then_succeeds() -> None:
    adapter, session = provider(
        [FakeResponse({}, status_code=503), FakeResponse(page([ticketmaster_event()]))]
    )

    assert len(adapter.fetch_events()) == 1
    assert len(session.calls) == 2


def test_connection_failure_uses_bounded_retries() -> None:
    adapter, session = provider(
        [
            requests.ConnectionError("https://example.invalid/?apikey=test-secret"),
            requests.ConnectionError("again"),
            requests.ConnectionError("still unavailable"),
        ]
    )

    with pytest.raises(TicketmasterProviderError) as exc_info:
        adapter.fetch_events()

    assert "test-secret" not in str(exc_info.value)
    assert len(session.calls) == 3


def test_malformed_json_raises_sanitized_provider_error() -> None:
    adapter, _session = provider([FakeResponse(ValueError("bad JSON"))])

    with pytest.raises(TicketmasterProviderError, match="malformed JSON"):
        adapter.fetch_events()


def test_one_malformed_event_does_not_abort_page() -> None:
    malformed = ticketmaster_event(id=None)
    adapter, _session = provider(
        [FakeResponse(page([malformed, ticketmaster_event(id="valid")]))]
    )

    events = adapter.fetch_events()

    assert [event.external_id for event in events] == ["valid"]
    assert adapter.records_retrieved == 2
    assert adapter.records_skipped == 1


@pytest.mark.django_db
def test_repeated_ticketmaster_ingestion_updates_unique_source_record() -> None:
    first, _session = provider([FakeResponse(page([ticketmaster_event()]))])
    second_record = ticketmaster_event(info="Updated event information.")
    second, _session = provider([FakeResponse(page([second_record]))])

    first_stats = EventIngestionPipeline().ingest(first)
    second_stats = EventIngestionPipeline().ingest(second)

    assert first_stats.created == 1
    assert second_stats.updated == 1
    assert Event.objects.count() == 1
    assert EventSourceRecord.objects.count() == 1
    source = EventSourceRecord.objects.get()
    assert source.provider == "ticketmaster"
    assert source.external_id == "tm-123"
    assert source.raw_data["info"] == "Updated event information."
