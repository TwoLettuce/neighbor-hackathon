from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from events.classifiers.base import EventClassifier
from events.classifiers.rule_based import RuleBasedEventClassifier
from events.deduplication import EventDeduplicator
from events.domain.types import EventClassificationInput, NormalizedEvent
from events.ingestion.normalizer import EventNormalizer
from events.models import CareerField, Event, EventSourceRecord
from events.providers.base import EventProvider
from events.services.taxonomy import CAREER_TAXONOMY


@dataclass
class IngestionStats:
    retrieved: int = 0
    normalized: int = 0
    matched: int = 0
    created: int = 0
    updated: int = 0
    failed: int = 0


class EventIngestionPipeline:
    def __init__(
        self,
        classifier: EventClassifier | None = None,
        normalizer: EventNormalizer | None = None,
        deduplicator: EventDeduplicator | None = None,
    ) -> None:
        self.classifier = classifier or RuleBasedEventClassifier()
        self.normalizer = normalizer or EventNormalizer()
        self.deduplicator = deduplicator or EventDeduplicator()

    def ingest(self, provider: EventProvider) -> IngestionStats:
        raw_events = provider.fetch_events()
        stats = IngestionStats(retrieved=len(raw_events))
        for raw in raw_events:
            try:
                normalized = self.normalizer.normalize(raw)
                stats.normalized += 1
                result = self._persist(normalized)
                setattr(stats, result, getattr(stats, result) + 1)
            except (ValueError, TypeError):
                stats.failed += 1
        return stats

    @transaction.atomic
    def _persist(self, item: NormalizedEvent) -> str:
        now = timezone.now()
        source = (
            EventSourceRecord.objects.select_related("event")
            .filter(provider=item.provider, external_id=item.external_id)
            .first()
        )
        if source:
            event = source.event
            result = "updated"
        else:
            event, _score = self.deduplicator.find_match(item)
            result = "matched" if event else "created"
            if event is None:
                event = Event(first_seen_at=now, last_seen_at=now)

        classification = self.classifier.classify(
            EventClassificationInput(
                title=item.title,
                description=item.description,
                format_hint=item.format,
                organizer_name=item.organizer_name,
            )
        )
        fields = {
            "title": item.title,
            "description": item.description,
            "start_time": item.start_time,
            "end_time": item.end_time,
            "timezone": item.timezone,
            "format": classification.format,
            "organizer_name": item.organizer_name,
            "organizer_url": item.organizer_url,
            "venue_name": item.venue_name,
            "address": item.address,
            "city": item.city,
            "state_region": item.state_region,
            "country": item.country,
            "location": item.location,
            "topic_tags": classification.topics,
            "likely_attendee_types": classification.likely_attendee_types,
            "experience_levels": classification.experience_levels,
            "networking_relevant": classification.networking_relevant,
            "networking_strength": classification.networking_strength,
            "quality_score": self._quality(item),
            "last_seen_at": now,
        }
        for name, value in fields.items():
            setattr(event, name, value)
        event.full_clean(exclude=["career_fields"])
        event.save()
        event.career_fields.set(self._career_fields(classification.career_fields))

        if source:
            source.source_url = item.source_url
            source.raw_data = item.raw_data
            source.last_seen_at = now
            source.save(update_fields=["source_url", "raw_data", "last_seen_at"])
        else:
            EventSourceRecord.objects.create(
                event=event,
                provider=item.provider,
                external_id=item.external_id,
                source_url=item.source_url,
                raw_data=item.raw_data,
                first_seen_at=now,
                last_seen_at=now,
            )
        return result

    @staticmethod
    def _career_fields(slugs: list[str]) -> list[CareerField]:
        fields = []
        for slug in slugs:
            definition = CAREER_TAXONOMY.get(slug)
            name = definition.name if definition else slug.replace("_", " ").title()
            field, _ = CareerField.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "keywords": list(definition.keywords) if definition else [],
                },
            )
            fields.append(field)
        return fields

    @staticmethod
    def _quality(item: NormalizedEvent) -> float:
        present = sum(
            bool(value)
            for value in (
                item.description,
                item.organizer_name,
                item.venue_name,
                item.location,
                item.end_time,
            )
        )
        return round(0.4 + present * 0.1, 2)
