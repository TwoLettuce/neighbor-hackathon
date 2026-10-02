from datetime import timedelta

import pytest
from django.utils import timezone
from events.models import CareerField, Event, EventFormat
from events.ranking import EventRanker


@pytest.mark.django_db
def test_technical_community_ranks_above_unrelated_networking_event() -> None:
    now = timezone.now()
    software = CareerField.objects.create(slug="software_engineering", name="Software Engineering")
    marketing = CareerField.objects.create(slug="marketing", name="Marketing")
    meetup = Event.objects.create(
        title="Python Developer Meetup",
        description="Python discussion and networking",
        start_time=now + timedelta(days=7),
        format=EventFormat.IN_PERSON,
        networking_relevant=True,
        networking_strength=0.9,
        quality_score=0.8,
        topic_tags=["python"],
        first_seen_at=now,
        last_seen_at=now,
    )
    meetup.career_fields.add(software)
    unrelated = Event.objects.create(
        title="Marketing Breakfast",
        description="Brand leadership networking",
        start_time=now + timedelta(days=7),
        format=EventFormat.IN_PERSON,
        networking_relevant=True,
        networking_strength=0.9,
        quality_score=0.8,
        topic_tags=["marketing"],
        first_seen_at=now,
        last_seen_at=now,
    )
    unrelated.career_fields.add(marketing)

    ranker = EventRanker()
    developer_score = ranker.rank(meetup, {"software_engineering"}, 10, 50, now).total_score
    unrelated_score = ranker.rank(unrelated, {"software_engineering"}, 10, 50, now).total_score

    assert developer_score > unrelated_score + 0.25
