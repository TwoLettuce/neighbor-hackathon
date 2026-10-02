import re
from dataclasses import dataclass
from datetime import timedelta
from difflib import SequenceMatcher

from django.contrib.gis.geos import Point

from events.domain.types import NormalizedEvent
from events.models import Event


@dataclass(frozen=True)
class DeduplicationResult:
    score: float
    title_similarity: float
    time_similarity: float
    location_similarity: float
    organizer_similarity: float

    @property
    def is_duplicate(self) -> bool:
        return self.score >= 0.82


def _clean(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, _clean(left), _clean(right)).ratio()


class EventDeduplicator:
    threshold = 0.82

    def score(self, candidate: NormalizedEvent, event: Event) -> DeduplicationResult:
        title = _similarity(candidate.title, event.title)
        delta_seconds = abs((candidate.start_time - event.start_time).total_seconds())
        time = max(0.0, 1.0 - delta_seconds / (3 * 60 * 60))
        location = self._location_similarity(candidate.location, event.location)
        organizer = _similarity(candidate.organizer_name, event.organizer_name)
        total = title * 0.4 + time * 0.25 + location * 0.2 + organizer * 0.15
        return DeduplicationResult(round(total, 4), title, time, location, organizer)

    def find_match(
        self, candidate: NormalizedEvent
    ) -> tuple[Event | None, DeduplicationResult | None]:
        window = timedelta(hours=3)
        possible = Event.objects.filter(
            start_time__gte=candidate.start_time - window,
            start_time__lte=candidate.start_time + window,
        )
        best_event: Event | None = None
        best_result: DeduplicationResult | None = None
        for event in possible:
            result = self.score(candidate, event)
            if best_result is None or result.score > best_result.score:
                best_event, best_result = event, result
        if best_result and best_result.score >= self.threshold:
            return best_event, best_result
        return None, best_result

    @staticmethod
    def _location_similarity(left: Point | None, right: Point | None) -> float:
        if left is None or right is None:
            return 0.0
        # GEOS distance is degrees for SRID 4326; sufficient for a bounded comparison.
        miles = left.distance(right) * 69.0
        return max(0.0, 1.0 - miles / 10.0)
