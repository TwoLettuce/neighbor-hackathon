from datetime import datetime
import os
from typing import Any
from urllib.parse import urlencode

from django.utils import timezone
from django.utils.dateparse import parse_datetime
import requests

from events.domain.types import RawEvent
from events.providers.base import EventProvider, ProviderUnavailableError


class TicketmasterProvider(EventProvider):
    """Real adapter for fetching events via the Ticketmaster Discovery API (v2)."""

    name = "ticketmaster"
    BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

    def __init__(
        self,
        api_key: str | None = None,
        keyword: str | None = None,
        city: str | None = None,
        state_code: str | None = None,
        country_code: str = "US",
        size: int = 50,
    ) -> None:
        self.api_key = api_key or os.getenv("TICKETMASTER")
        self.keyword = keyword
        self.city = city
        self.state_code = state_code
        self.country_code = country_code
        self.size = size

    def fetch_events(self) -> list[RawEvent]:
        if not self.api_key:
            raise ProviderUnavailableError(
                "Ticketmaster API key is not configured. "
                "Please set the 'TICKETMASTER' environment variable in your .env file."
            )

        params: dict[str, Any] = {
            "apikey": self.api_key,
            "size": self.size,
            "countryCode": self.country_code,
            "sort": "date,asc",
        }
        if self.keyword:
            params["keyword"] = self.keyword
        if self.city:
            params["city"] = self.city
        if self.state_code:
            params["stateCode"] = self.state_code

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=20,
                headers={"User-Agent": "NeighborEvents/1.0"},
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise ProviderUnavailableError(f"Failed to fetch events from Ticketmaster: {exc}") from exc

        events_data = data.get("_embedded", {}).get("events", [])
        raw_events: list[RawEvent] = []

        for item in events_data:
            parsed_event = self._parse_event(item)
            if parsed_event:
                raw_events.append(parsed_event)

        return raw_events

    def _parse_event(self, item: dict[str, Any]) -> RawEvent | None:
        external_id = str(item.get("id") or "").strip()
        title = item.get("name", "").strip()
        source_url = item.get("url", "").strip()

        if not external_id or not title:
            return None
        if not source_url.startswith(("http://", "https://")):
            source_url = f"https://www.ticketmaster.com/event/{external_id}"

        # Parse start date/time
        dates = item.get("dates", {})
        start_info = dates.get("start", {})
        timezone_str = dates.get("timezone", "America/Denver") or "America/Denver"

        start_time: datetime | None = None
        start_dt_str = start_info.get("dateTime")
        if start_dt_str:
            start_time = parse_datetime(start_dt_str)
        elif start_info.get("localDate"):
            local_date = start_info["localDate"]
            local_time = start_info.get("localTime", "00:00:00")
            start_time = parse_datetime(f"{local_date}T{local_time}")

        if not start_time:
            return None

        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)

        # Parse end date/time if available
        end_info = dates.get("end", {})
        end_time: datetime | None = None
        end_dt_str = end_info.get("dateTime")
        if end_dt_str:
            end_time = parse_datetime(end_dt_str)
            if end_time and timezone.is_naive(end_time):
                end_time = timezone.make_aware(end_time)

        # Description and additional notes
        description_parts = []
        if item.get("description"):
            description_parts.append(item["description"])
        if item.get("info"):
            description_parts.append(item["info"])
        if item.get("pleaseNote"):
            description_parts.append(item["pleaseNote"])
        
        # Include classifications/genres in description for taxonomy matching
        classifications = item.get("classifications", [])
        genre_tags = []
        for c in classifications:
            for key in ("segment", "genre", "subGenre"):
                val = c.get(key, {}).get("name")
                if val and val not in ("Undefined", "Other"):
                    genre_tags.append(val)
        if genre_tags:
            description_parts.append(f"Categories: {', '.join(genre_tags)}")

        description = "\n\n".join(description_parts)

        # Venue information
        venues = item.get("_embedded", {}).get("venues", [])
        venue_name = ""
        address = ""
        city = ""
        state_region = ""
        country = self.country_code
        latitude = None
        longitude = None

        if venues and isinstance(venues, list):
            venue = venues[0]
            venue_name = venue.get("name", "")
            address_line = venue.get("address", {}).get("line1", "")
            address = address_line
            city = venue.get("city", {}).get("name", "")
            state_region = venue.get("state", {}).get("stateCode", "") or venue.get("state", {}).get("name", "")
            country = venue.get("country", {}).get("countryCode", "US")
            
            location_info = venue.get("location", {})
            try:
                if "latitude" in location_info and "longitude" in location_info:
                    latitude = float(location_info["latitude"])
                    longitude = float(location_info["longitude"])
            except (ValueError, TypeError):
                latitude = None
                longitude = None

        # Organizer / Promoters
        organizer_name = ""
        promoters = item.get("promoters", [])
        if promoters and isinstance(promoters, list):
            organizer_name = promoters[0].get("name", "")
        if not organizer_name and venues:
            organizer_name = venue_name

        return RawEvent(
            provider=self.name,
            external_id=external_id,
            source_url=source_url,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            timezone=timezone_str,
            format_hint="IN_PERSON",
            organizer_name=organizer_name,
            organizer_url="",
            venue_name=venue_name,
            address=address,
            city=city,
            state_region=state_region,
            country=country,
            latitude=latitude,
            longitude=longitude,
            raw_data={"id": external_id, "url": source_url, "name": title},
        )
