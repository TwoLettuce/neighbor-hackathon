from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

from events.models import Event, EventFormat
from events.services.taxonomy import CAREER_TAXONOMY, related_careers


@dataclass(frozen=True)
class EventRanking:
    total_score: float
    career_match: float
    networking_score: float
    distance_score: float
    topic_score: float
    quality_score: float
    time_score: float


class EventRanker:
    WEIGHTS = {
        "career_match": 0.35,
        "networking_score": 0.20,
        "distance_score": 0.15,
        "topic_score": 0.10,
        "quality_score": 0.10,
        "time_score": 0.10,
    }

    def rank(
        self,
        event: Event,
        target_careers: set[str],
        distance_miles: float | None,
        radius_miles: float,
        now: datetime | None = None,
    ) -> EventRanking:
        now = now or timezone.now()
        event_careers = {career.slug for career in event.career_fields.all()}
        expanded = related_careers(target_careers)
        direct = bool(event_careers & target_careers)
        related = bool(event_careers & expanded)
        career_match = 1.0 if direct else 0.72 if related else 0.0

        keywords = {
            keyword.strip()
            for slug in expanded
            if slug in CAREER_TAXONOMY
            for keyword in CAREER_TAXONOMY[slug].keywords
        }
        searchable = " ".join([*event.topic_tags, event.title.lower(), event.description.lower()])
        matches = sum(keyword in searchable for keyword in keywords)
        topic_score = min(1.0, matches / 3) if keywords else 0.0

        if event.format == EventFormat.LIVE_VIRTUAL:
            distance_score = 0.7
        elif distance_miles is None:
            distance_score = 0.0
        else:
            distance_score = max(0.0, 1 - distance_miles / max(radius_miles, 1))

        days_away = max(0.0, (event.start_time - now).total_seconds() / 86400)
        time_score = max(0.2, 1 - days_away / 120)
        components = {
            "career_match": career_match,
            "networking_score": event.networking_strength,
            "distance_score": distance_score,
            "topic_score": topic_score,
            "quality_score": event.quality_score,
            "time_score": time_score,
        }
        total = sum(components[name] * weight for name, weight in self.WEIGHTS.items())
        return EventRanking(total_score=round(total, 3), **components)

    @staticmethod
    def explanation(event: Event, ranking: EventRanking, distance_miles: float | None) -> str:
        strength = "Strong match" if ranking.total_score >= 0.75 else "Good match"
        format_label = event.get_format_display().lower()
        topics = ", ".join(tag.replace("_", " ") for tag in event.topic_tags[:2])
        subject = f"{topics} " if topics else ""
        distance = f" and is {distance_miles:.0f} miles away" if distance_miles is not None else ""
        return (
            f"{strength} because this is a {format_label} {subject}event with "
            f"{'strong' if event.networking_strength >= 0.75 else 'useful'} "
            f"networking opportunities{distance}."
        )
