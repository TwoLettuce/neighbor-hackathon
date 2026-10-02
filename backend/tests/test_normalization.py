from datetime import datetime

import pytest
from django.utils import timezone
from events.domain.types import RawEvent
from events.ingestion.normalizer import EventNormalizer


def test_provider_record_normalizes_without_leaking_provider_fields() -> None:
    raw = RawEvent(
        provider="ExampleFeed",
        external_id="abc-123",
        source_url="https://events.example/abc",
        title="  Python   Meetup  ",
        start_time=datetime(2026, 10, 8, 19),
        latitude=40.2338,
        longitude=-111.6585,
        raw_data={"provider_specific_name": "value"},
    )

    result = EventNormalizer().normalize(raw)

    assert result.provider == "examplefeed"
    assert result.title == "Python Meetup"
    assert timezone.is_aware(result.start_time)
    assert result.location.x == pytest.approx(-111.6585)
    assert result.raw_data["provider_specific_name"] == "value"


def test_normalizer_rejects_unsafe_source_url() -> None:
    raw = RawEvent(
        provider="feed",
        external_id="1",
        source_url="javascript:alert(1)",
        title="Event",
        start_time=timezone.now(),
    )

    with pytest.raises(ValueError, match="HTTP"):
        EventNormalizer().normalize(raw)
