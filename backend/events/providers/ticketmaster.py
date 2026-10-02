import logging
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from datetime import timezone as datetime_timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pygeohash
import requests
from django.utils import timezone

from events.domain.types import RawEvent
from events.models import EventFormat
from events.providers.base import EventProvider, ProviderUnavailableError

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
MAX_DEEP_PAGING_RESULTS = 1000


class TicketmasterProviderError(ProviderUnavailableError):
    """A sanitized Ticketmaster failure safe to show in command output."""


class TicketmasterProvider(EventProvider):
    name = "ticketmaster"

    def __init__(
        self,
        *,
        api_key: str,
        latitude: float,
        longitude: float,
        radius_miles: float,
        days: int = 90,
        keyword: str | None = None,
        country_code: str = "US",
        max_pages: int = 10,
        page_size: int = 100,
        base_url: str = DEFAULT_BASE_URL,
        timeout: tuple[float, float] = (5, 20),
        max_retries: int = 2,
        session: requests.Session | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        request_interval: float = 0.5,
        now: datetime | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("TICKETMASTER_API_KEY is required")
        radius_value = float(radius_miles)
        if radius_value <= 0 or radius_value > 19_999 or not radius_value.is_integer():
            raise ValueError(
                "Ticketmaster radius must be a whole number between 1 and 19,999 miles"
            )
        if days <= 0:
            raise ValueError("Ticketmaster date window must be greater than zero")
        if max_pages <= 0:
            raise ValueError("Ticketmaster max pages must be greater than zero")
        if not 1 <= page_size <= 200:
            raise ValueError("Ticketmaster page size must be between 1 and 200")

        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.radius_miles = int(radius_value)
        self.days = days
        self.keyword = keyword
        self.country_code = country_code
        self.max_pages = min(
            max_pages,
            (MAX_DEEP_PAGING_RESULTS + page_size - 1) // page_size,
        )
        self.page_size = page_size
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = session or requests.Session()
        self.sleeper = sleeper
        self.clock = clock
        self.request_interval = request_interval
        self.window_start = now or timezone.now()
        if timezone.is_naive(self.window_start):
            self.window_start = timezone.make_aware(
                self.window_start, datetime_timezone.utc
            )
        self.window_end = self.window_start + timedelta(days=days)
        self._last_request_at: float | None = None

        self.pages_fetched = 0
        self.records_retrieved = 0
        self.records_skipped = 0

    def fetch_events(self) -> list[RawEvent]:
        events: list[RawEvent] = []
        page_number = 0

        while page_number < self.max_pages:
            payload = self._request_page(page_number)
            self.pages_fetched += 1
            embedded = payload.get("_embedded")
            records = embedded.get("events", []) if isinstance(embedded, dict) else []
            if not isinstance(records, list):
                raise TicketmasterProviderError(
                    "Ticketmaster returned an invalid events collection"
                )

            self.records_retrieved += len(records)
            for record in records:
                try:
                    if not isinstance(record, dict):
                        raise ValueError("Event record is not an object")
                    event = self._to_raw_event(record)
                    if not self.window_start <= event.start_time <= self.window_end:
                        raise ValueError("Event is outside the requested window")
                    events.append(event)
                except (KeyError, TypeError, ValueError, ZoneInfoNotFoundError):
                    self.records_skipped += 1
                    logger.warning("Skipped malformed Ticketmaster event record")

            page = payload.get("page")
            if not records or not isinstance(page, dict):
                break
            total_pages = page.get("totalPages")
            if not isinstance(total_pages, int) or page_number + 1 >= total_pages:
                break

            page_number += 1
            if page_number * self.page_size >= MAX_DEEP_PAGING_RESULTS:
                break

        return events

    def _request_page(self, page_number: int) -> dict[str, Any]:
        params: dict[str, str | int | float] = {
            "apikey": self.api_key,
            "geoPoint": pygeohash.encode(
                latitude=self.latitude,
                longitude=self.longitude,
                precision=9,
            ),
            "radius": self.radius_miles,
            "unit": "miles",
            "countryCode": self.country_code,
            "startDateTime": self._utc_parameter(self.window_start),
            "endDateTime": self._utc_parameter(self.window_end),
            "sort": "date,asc",
            "size": self.page_size,
            "page": page_number,
        }
        if self.keyword:
            params["keyword"] = self.keyword

        for attempt in range(self.max_retries + 1):
            self._pace_request()
            try:
                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=self.timeout,
                    headers={"User-Agent": "NeighborEvents/1.0"},
                )
            except (requests.Timeout, requests.ConnectionError):
                if attempt < self.max_retries:
                    self.sleeper(0.5 * (2**attempt))
                    continue
                raise TicketmasterProviderError(
                    "Ticketmaster request failed after bounded retries"
                ) from None
            except requests.RequestException:
                raise TicketmasterProviderError("Ticketmaster request failed") from None

            self._log_rate_limit_headers(response)
            if response.status_code in {401, 403}:
                raise TicketmasterProviderError(
                    "Ticketmaster rejected the configured API credentials"
                )
            if response.status_code == 429 or 500 <= response.status_code < 600:
                if attempt < self.max_retries:
                    self.sleeper(self._retry_delay(response, attempt))
                    continue
                raise TicketmasterProviderError(
                    f"Ticketmaster remained unavailable (HTTP {response.status_code})"
                )
            if response.status_code >= 400:
                raise TicketmasterProviderError(
                    f"Ticketmaster request failed (HTTP {response.status_code})"
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise TicketmasterProviderError(
                    "Ticketmaster returned malformed JSON"
                ) from exc
            if not isinstance(payload, dict):
                raise TicketmasterProviderError(
                    "Ticketmaster returned an invalid JSON response"
                )
            return payload

        raise TicketmasterProviderError("Ticketmaster request failed")

    def _pace_request(self) -> None:
        if self._last_request_at is not None:
            remaining = self.request_interval - (self.clock() - self._last_request_at)
            if remaining > 0:
                self.sleeper(remaining)
        self._last_request_at = self.clock()

    @staticmethod
    def _retry_delay(response: requests.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        try:
            return min(max(float(retry_after), 0.0), 10.0)
        except (TypeError, ValueError):
            return 0.5 * (2**attempt)

    @staticmethod
    def _log_rate_limit_headers(response: requests.Response) -> None:
        names = (
            "Rate-Limit-Available",
            "Rate-Limit-Reset",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        )
        values = {name: response.headers[name] for name in names if name in response.headers}
        if values:
            logger.debug("Ticketmaster rate-limit headers: %s", values)

    def _to_raw_event(self, record: dict[str, Any]) -> RawEvent:
        external_id = self._required_string(record, "id")
        title = self._required_string(record, "name")
        source_url = self._required_string(record, "url")

        embedded = record.get("_embedded")
        venues = embedded.get("venues", []) if isinstance(embedded, dict) else []
        venue = venues[0] if venues and isinstance(venues[0], dict) else {}
        dates = record.get("dates") if isinstance(record.get("dates"), dict) else {}
        start_data = dates.get("start") if isinstance(dates.get("start"), dict) else {}
        end_data = dates.get("end") if isinstance(dates.get("end"), dict) else {}
        timezone_name = str(dates.get("timezone") or venue.get("timezone") or "UTC")
        start_time = self._event_datetime(start_data, timezone_name, required=True)
        end_time = self._event_datetime(end_data, timezone_name, required=False)

        address_data = venue.get("address") if isinstance(venue.get("address"), dict) else {}
        address = ", ".join(
            str(address_data[key]).strip()
            for key in ("line1", "line2")
            if address_data.get(key)
        )
        city = self._nested_name(venue, "city")
        state_region = self._nested_value(venue, "state", "stateCode") or self._nested_name(
            venue, "state"
        )
        country = self._nested_value(venue, "country", "countryCode") or self.country_code
        location = venue.get("location") if isinstance(venue.get("location"), dict) else {}
        latitude = self._optional_float(location.get("latitude"))
        longitude = self._optional_float(location.get("longitude"))

        descriptions = [
            str(record[key]).strip()
            for key in ("info", "pleaseNote", "description")
            if record.get(key)
        ]
        description = "\n\n".join(dict.fromkeys(descriptions))
        promoter = record.get("promoter") if isinstance(record.get("promoter"), dict) else {}
        source_categories = self._classification_names(record.get("classifications"))
        has_physical_venue = bool(
            venue.get("name") or address or (latitude is not None and longitude is not None)
        )

        return RawEvent(
            provider=self.name,
            external_id=external_id,
            source_url=source_url,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone_name,
            format_hint=EventFormat.IN_PERSON if has_physical_venue else EventFormat.OTHER,
            organizer_name=str(promoter.get("name") or "").strip(),
            venue_name=str(venue.get("name") or "").strip(),
            address=address,
            city=city,
            state_region=state_region,
            country=country,
            latitude=latitude,
            longitude=longitude,
            source_categories=source_categories,
            raw_data=record,
        )

    @staticmethod
    def _event_datetime(
        value: dict[str, Any],
        timezone_name: str,
        *,
        required: bool,
    ) -> datetime | None:
        date_time = value.get("dateTime")
        if date_time:
            parsed = datetime.fromisoformat(str(date_time).replace("Z", "+00:00"))
            if timezone.is_naive(parsed):
                parsed = parsed.replace(tzinfo=datetime_timezone.utc)
            return parsed

        local_date = value.get("localDate")
        local_time = value.get("localTime")
        if local_date and local_time:
            parsed = datetime.fromisoformat(f"{local_date}T{local_time}")
            return parsed.replace(tzinfo=ZoneInfo(timezone_name))
        if required:
            raise ValueError("Ticketmaster event has no precise start time")
        return None

    @staticmethod
    def _classification_names(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        names: list[str] = []
        for classification in value:
            if not isinstance(classification, dict):
                continue
            for level in ("segment", "genre", "subGenre", "type", "subType"):
                item = classification.get(level)
                name = item.get("name") if isinstance(item, dict) else None
                if name and str(name).lower() != "undefined":
                    names.append(str(name).strip())
        return list(dict.fromkeys(names))

    @staticmethod
    def _required_string(record: dict[str, Any], key: str) -> str:
        value = record.get(key)
        if not value or not isinstance(value, str):
            raise ValueError(f"Ticketmaster event is missing {key}")
        return value.strip()

    @staticmethod
    def _nested_name(record: dict[str, Any], key: str) -> str:
        return TicketmasterProvider._nested_value(record, key, "name")

    @staticmethod
    def _nested_value(record: dict[str, Any], key: str, child: str) -> str:
        value = record.get(key)
        if not isinstance(value, dict):
            return ""
        return str(value.get(child) or "").strip()

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _utc_parameter(value: datetime) -> str:
        return value.astimezone(datetime_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
