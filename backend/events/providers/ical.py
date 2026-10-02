from datetime import date, datetime, time
from urllib.parse import urlparse

import requests
from django.utils import timezone
from icalendar import Calendar

from events.domain.types import RawEvent
from events.providers.base import EventProvider


class ICalProvider(EventProvider):
    """Real adapter for a preconfigured public iCalendar feed."""

    name = "ical"

    def __init__(self, feed_url: str, provider_name: str = "ical") -> None:
        parsed = urlparse(feed_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("iCal feed URL must be an absolute HTTP(S) URL")
        self.feed_url = feed_url
        self.name = provider_name

    def fetch_events(self) -> list[RawEvent]:
        response = requests.get(
            self.feed_url,
            timeout=20,
            headers={"User-Agent": "Job'n'WeaveEvents/1.0"},
        )
        response.raise_for_status()
        calendar = Calendar.from_ical(response.content)
        events: list[RawEvent] = []
        for component in calendar.walk("VEVENT"):
            start = self._datetime(component.decoded("DTSTART"))
            end_value = component.get("DTEND")
            end = self._datetime(end_value.dt) if end_value else None
            uid = str(component.get("UID", f"{start.isoformat()}-{component.get('SUMMARY')}"))
            url = str(component.get("URL", self.feed_url))
            events.append(
                RawEvent(
                    provider=self.name,
                    external_id=uid,
                    source_url=url,
                    title=str(component.get("SUMMARY", "Untitled event")),
                    description=str(component.get("DESCRIPTION", "")),
                    start_time=start,
                    end_time=end,
                    venue_name=str(component.get("LOCATION", "")),
                    raw_data={"uid": uid, "feed_url": self.feed_url},
                )
            )
        return events

    @staticmethod
    def _datetime(value: date | datetime) -> datetime:
        if isinstance(value, datetime):
            return value if timezone.is_aware(value) else timezone.make_aware(value)
        return timezone.make_aware(datetime.combine(value, time.min))
