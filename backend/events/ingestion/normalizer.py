from django.contrib.gis.geos import Point
from django.utils import timezone

from events.domain.types import NormalizedEvent, RawEvent
from events.models import EventFormat


class EventNormalizer:
    def normalize(self, raw: RawEvent) -> NormalizedEvent:
        title = " ".join(raw.title.split())
        if not title:
            raise ValueError("Event title is required")
        if not raw.source_url.startswith(("https://", "http://")):
            raise ValueError("Event source URL must use HTTP(S)")

        start = raw.start_time
        if timezone.is_naive(start):
            start = timezone.make_aware(start)
        end = raw.end_time
        if end and timezone.is_naive(end):
            end = timezone.make_aware(end)
        location = None
        if raw.latitude is not None and raw.longitude is not None:
            location = Point(raw.longitude, raw.latitude, srid=4326)

        hint = raw.format_hint.upper().replace(" ", "_")
        event_format = hint if hint in EventFormat.values else EventFormat.OTHER
        return NormalizedEvent(
            provider=raw.provider.lower().strip(),
            external_id=str(raw.external_id).strip(),
            source_url=raw.source_url,
            title=title,
            description=raw.description.strip(),
            start_time=start,
            end_time=end,
            timezone=raw.timezone,
            format=event_format,
            organizer_name=raw.organizer_name.strip(),
            organizer_url=raw.organizer_url,
            venue_name=raw.venue_name.strip(),
            address=raw.address.strip(),
            city=raw.city.strip(),
            state_region=raw.state_region.strip(),
            country=raw.country.upper(),
            location=location,
            source_categories=list(dict.fromkeys(raw.source_categories)),
            raw_data=raw.raw_data,
        )
