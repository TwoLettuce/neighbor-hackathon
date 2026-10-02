from dataclasses import asdict
from datetime import date, timedelta

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import Q
from django.utils import timezone

from events.models import Event, EventFormat, EventStatus
from events.ranking import EventRanker
from events.services.geocoding import GeocodingService
from events.services.taxonomy import resolve_career


class EventSearchService:
    def __init__(self, geocoder: GeocodingService, ranker: EventRanker | None = None) -> None:
        self.geocoder = geocoder
        self.ranker = ranker or EventRanker()

    def search(
        self,
        *,
        career: str,
        location: str,
        radius_miles: float,
        start_date: date | None = None,
        end_date: date | None = None,
        formats: list[str] | None = None,
    ) -> list[dict]:
        now = timezone.now()
        origin = self.geocoder.geocode(location)
        selected_formats = formats or [
            EventFormat.IN_PERSON,
            EventFormat.HYBRID,
            EventFormat.LIVE_VIRTUAL,
        ]
        query = (
            Event.objects.filter(
                networking_relevant=True,
                format__in=selected_formats,
                status=EventStatus.APPROVED,
            )
            .filter(
                Q(end_time__gte=now)
                | Q(
                    end_time__isnull=True,
                    start_time__gte=now - timedelta(hours=3),
                )
            )
            .filter(
                Q(location__distance_lte=(origin, D(mi=radius_miles)))
                | Q(format=EventFormat.LIVE_VIRTUAL)
            )
            .annotate(distance=Distance("location", origin))
            .prefetch_related("career_fields", "source_records")
        )
        if start_date:
            query = query.filter(start_time__date__gte=start_date)
        if end_date:
            query = query.filter(start_time__date__lte=end_date)

        target_careers = resolve_career(career)
        results = []
        for event in query:
            distance_miles = event.distance.mi if event.distance is not None else None
            ranking = self.ranker.rank(
                event,
                target_careers,
                distance_miles,
                radius_miles,
                query_text=career,
            )
            if (
                max(ranking.query_match, ranking.career_match, ranking.topic_score) == 0
                or ranking.total_score < 0.3
            ):
                continue
            source = next(iter(event.source_records.all()), None)
            results.append(
                {
                    "event": event,
                    "distance_miles": (
                        round(distance_miles, 1) if distance_miles is not None else None
                    ),
                    "match_score": ranking.total_score,
                    "score_breakdown": asdict(ranking),
                    "match_explanation": self.ranker.explanation(event, ranking, distance_miles),
                    "source_url": source.source_url if source else "",
                    "source_provider": source.provider if source else "",
                }
            )
        return sorted(results, key=lambda item: item["match_score"], reverse=True)[:50]
