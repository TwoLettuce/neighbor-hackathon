import pytest
from django.core.management import call_command
from events.models import Event, EventSourceRecord
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_seed_ingestion_is_idempotent() -> None:
    call_command("ingest_events", provider="seed")
    first_counts = (Event.objects.count(), EventSourceRecord.objects.count())

    call_command("ingest_events", provider="seed")

    assert first_counts == (24, 24)
    assert (Event.objects.count(), EventSourceRecord.objects.count()) == first_counts


@pytest.mark.django_db
def test_search_api_ranks_relevant_events_and_applies_radius() -> None:
    call_command("ingest_events", provider="seed")
    response = APIClient().get(
        "/api/events/search/",
        {
            "career": "Software Engineer",
            "location": "Provo, UT",
            "radius_miles": 10,
            "formats": ["IN_PERSON", "HYBRID", "LIVE_VIRTUAL"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] > 0
    titles = [event["title"] for event in payload["events"]]
    assert "Rust Wasatch Community Night" in titles
    if "Startup Founders Friday Mixer" in titles:
        assert titles.index("Rust Wasatch Community Night") < titles.index(
            "Startup Founders Friday Mixer"
        )
    for event in payload["events"]:
        if event["format"] != "LIVE_VIRTUAL":
            assert event["distance_miles"] <= 10
        assert event["source_url"].startswith("https://")
        assert "match_explanation" in event
