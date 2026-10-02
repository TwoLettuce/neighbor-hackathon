from datetime import timedelta

import pytest
from django.utils import timezone
from events.models import Event, EventSourceRecord, EventStatus
from rest_framework.test import APIClient


def submission_payload(**overrides) -> dict:
    start = timezone.now() + timedelta(days=7)
    values = {
        "title": "Python Networking Night",
        "description": "Meet local software developers for Django discussions and networking.",
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=2)).isoformat(),
        "timezone": "America/Denver",
        "format": "IN_PERSON",
        "organizer_name": "Utah Python Community",
        "organizer_url": "https://example.com/organizer",
        "venue_name": "Community Hall",
        "address": "100 Center Street",
        "city": "Provo",
        "state_region": "UT",
        "event_url": "https://example.com/python-night",
    }
    values.update(overrides)
    return values


@pytest.mark.django_db
def test_user_can_create_an_approved_event() -> None:
    response = APIClient().post(
        "/api/events/",
        submission_payload(),
        format="json",
    )

    assert response.status_code == 201
    event = Event.objects.get(pk=response.json()["id"])
    source = EventSourceRecord.objects.get(event=event)
    assert event.title == "Python Networking Night"
    assert event.status == EventStatus.APPROVED
    assert event.location is not None
    assert event.networking_relevant
    assert source.provider == "user_submitted"
    assert source.source_url == "https://example.com/python-night"


@pytest.mark.django_db
def test_submission_rejects_missing_required_fields() -> None:
    response = APIClient().post(
        "/api/events/",
        submission_payload(title=""),
        format="json",
    )

    assert response.status_code == 400
    assert "title" in response.json()
    assert Event.objects.count() == 0


@pytest.mark.django_db
def test_in_person_submission_requires_a_location() -> None:
    response = APIClient().post(
        "/api/events/",
        submission_payload(venue_name="", address="", city="", state_region=""),
        format="json",
    )

    assert response.status_code == 400
    assert {"venue_name", "city", "state_region"} <= response.json().keys()


@pytest.mark.django_db
def test_submission_rejects_end_before_start() -> None:
    start = timezone.now() + timedelta(days=7)
    response = APIClient().post(
        "/api/events/",
        submission_payload(
            start_time=start.isoformat(),
            end_time=(start - timedelta(hours=1)).isoformat(),
        ),
        format="json",
    )

    assert response.status_code == 400
    assert "end_time" in response.json()


@pytest.mark.django_db
def test_submission_rejects_malformed_url() -> None:
    response = APIClient().post(
        "/api/events/",
        submission_payload(event_url="not a valid URL"),
        format="json",
    )

    assert response.status_code == 400
    assert "event_url" in response.json()


@pytest.mark.django_db
def test_submission_rejects_an_obvious_duplicate() -> None:
    client = APIClient()
    first = client.post("/api/events/", submission_payload(), format="json")
    duplicate = client.post("/api/events/", submission_payload(), format="json")

    assert first.status_code == 201
    assert duplicate.status_code == 400
    assert "similar event already exists" in duplicate.json()["non_field_errors"][0]
    assert Event.objects.count() == 1


@pytest.mark.django_db
def test_user_submitted_event_appears_in_existing_search() -> None:
    client = APIClient()
    created = client.post("/api/events/", submission_payload(), format="json")

    response = client.get(
        "/api/events/search/",
        {
            "career": "Software Engineer",
            "location": "Provo, UT",
            "radius_miles": 10,
            "formats": ["IN_PERSON"],
        },
    )

    assert created.status_code == 201
    assert response.status_code == 200
    result = next(
        event
        for event in response.json()["events"]
        if event["id"] == created.json()["id"]
    )
    assert result["source_provider"] == "user_submitted"
    assert result["source_url"] == "https://example.com/python-night"


@pytest.mark.django_db
def test_search_prioritizes_partial_title_and_typo_matches() -> None:
    client = APIClient()
    created = client.post("/api/events/", submission_payload(), format="json")

    for query in ("Python Network", "Pyton Networkng"):
        response = client.get(
            "/api/events/search/",
            {
                "career": query,
                "location": "Provo, UT",
                "radius_miles": 10,
                "formats": ["IN_PERSON"],
            },
        )

        assert response.status_code == 200
        assert response.json()["events"][0]["id"] == created.json()["id"]
        assert response.json()["events"][0]["score_breakdown"]["query_match"] >= 0.75


@pytest.mark.django_db
def test_search_does_not_return_irrelevant_events_for_unknown_query() -> None:
    client = APIClient()
    client.post("/api/events/", submission_payload(), format="json")

    response = client.get(
        "/api/events/search/",
        {
            "career": "zzzxqv",
            "location": "Provo, UT",
            "radius_miles": 10,
            "formats": ["IN_PERSON"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"count": 0, "events": []}
