import re
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher

from django.utils import timezone

from events.models import Event, EventFormat
from events.services.taxonomy import CAREER_TAXONOMY, related_careers


@dataclass(frozen=True)
class EventRanking:
    total_score: float
    query_match: float
    career_match: float
    networking_score: float
    distance_score: float
    topic_score: float
    quality_score: float
    time_score: float


class EventRanker:
    WEIGHTS = {
        "query_match": 0.40,
        "career_match": 0.25,
        "networking_score": 0.10,
        "distance_score": 0.08,
        "topic_score": 0.07,
        "quality_score": 0.05,
        "time_score": 0.05,
    }

    def rank(
        self,
        event: Event,
        target_careers: set[str],
        distance_miles: float | None,
        radius_miles: float,
        now: datetime | None = None,
        query_text: str = "",
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
        query_match = self._query_match(event, query_text)

        if event.format == EventFormat.LIVE_VIRTUAL:
            distance_score = 0.7
        elif distance_miles is None:
            distance_score = 0.0
        else:
            distance_score = max(0.0, 1 - distance_miles / max(radius_miles, 1))

        days_away = max(0.0, (event.start_time - now).total_seconds() / 86400)
        time_score = max(0.2, 1 - days_away / 120)
        components = {
            "query_match": query_match,
            "career_match": career_match,
            "networking_score": event.networking_strength,
            "distance_score": distance_score,
            "topic_score": topic_score,
            "quality_score": event.quality_score,
            "time_score": time_score,
        }
        total = sum(components[name] * weight for name, weight in self.WEIGHTS.items())
        return EventRanking(total_score=round(total, 3), **components)

    @classmethod
    def _query_match(cls, event: Event, query: str) -> float:
        query = cls._normalize(query)
        if not query:
            return 0.0

        title = cls._normalize(event.title)
        details = cls._normalize(
            " ".join(
                [
                    event.description,
                    event.organizer_name,
                    *event.topic_tags,
                    *(field.name for field in event.career_fields.all()),
                ]
            )
        )
        if query == title:
            return 1.0
        if query in title:
            return 0.95
        if query in details:
            return 0.75

        query_tokens = set(query.split())
        title_tokens = set(title.split())
        detail_tokens = set(details.split())
        title_coverage = len(query_tokens & title_tokens) / len(query_tokens)
        detail_coverage = len(query_tokens & (title_tokens | detail_tokens)) / len(query_tokens)

        phrase_similarity = SequenceMatcher(None, query, title).ratio()
        fuzzy_title_coverage = sum(
            any(
                event_token.startswith(query_token)
                or query_token.startswith(event_token)
                or SequenceMatcher(None, query_token, event_token).ratio() >= 0.78
                for event_token in title_tokens
            )
            for query_token in query_tokens
        ) / len(query_tokens)

        return round(
            max(
                title_coverage * 0.9,
                detail_coverage * 0.65,
                phrase_similarity * 0.85 if phrase_similarity >= 0.68 else 0.0,
                fuzzy_title_coverage * 0.9,
            ),
            3,
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", value.lower()))

    @staticmethod
    def explanation(event: Event, ranking: EventRanking, distance_miles: float | None) -> str:
        if ranking.query_match >= 0.75:
            return (
                "Strong match for your search"
                + (f" and {distance_miles:.0f} miles away." if distance_miles is not None else ".")
            )
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
