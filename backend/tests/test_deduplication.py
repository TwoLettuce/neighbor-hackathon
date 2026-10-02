from datetime import timedelta

from django.contrib.gis.geos import Point
from django.utils import timezone
from events.deduplication import EventDeduplicator
from events.domain.types import NormalizedEvent
from events.models import Event


def candidate(**overrides) -> NormalizedEvent:
    values = {
        "provider": "ical",
        "external_id": "other-id",
        "source_url": "https://example.com/event",
        "title": "UtahJS October Meetup",
        "description": "",
        "start_time": timezone.now() + timedelta(days=5),
        "end_time": None,
        "timezone": "America/Denver",
        "format": "IN_PERSON",
        "organizer_name": "UtahJS",
        "organizer_url": "",
        "venue_name": "Kiln",
        "address": "",
        "city": "Lehi",
        "state_region": "UT",
        "country": "US",
        "location": Point(-111.8508, 40.3916, srid=4326),
        "raw_data": {},
    }
    values.update(overrides)
    return NormalizedEvent(**values)


def test_duplicate_score_is_explainable_and_above_threshold() -> None:
    item = candidate()
    existing = Event(
        title="UtahJS October Meetup",
        start_time=item.start_time + timedelta(minutes=10),
        organizer_name="UtahJS",
        location=Point(-111.851, 40.392, srid=4326),
    )

    result = EventDeduplicator().score(item, existing)

    assert result.title_similarity == 1
    assert result.time_similarity > 0.9
    assert result.location_similarity > 0.9
    assert result.is_duplicate


def test_different_event_does_not_merge() -> None:
    item = candidate()
    existing = Event(
        title="Healthcare Leadership Breakfast",
        start_time=item.start_time,
        organizer_name="Utah Hospital Council",
        location=Point(-111.89, 40.76, srid=4326),
    )

    assert not EventDeduplicator().score(item, existing).is_duplicate
