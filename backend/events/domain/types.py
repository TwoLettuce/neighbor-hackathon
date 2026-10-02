from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from django.contrib.gis.geos import Point
from pydantic import BaseModel, Field

from events.models import EventFormat


@dataclass(frozen=True)
class RawEvent:
    provider: str
    external_id: str
    source_url: str
    title: str
    start_time: datetime
    end_time: datetime | None = None
    description: str = ""
    timezone: str = "America/Denver"
    format_hint: str = ""
    organizer_name: str = ""
    organizer_url: str = ""
    venue_name: str = ""
    address: str = ""
    city: str = ""
    state_region: str = ""
    country: str = "US"
    latitude: float | None = None
    longitude: float | None = None
    source_categories: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedEvent:
    provider: str
    external_id: str
    source_url: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime | None
    timezone: str
    format: str
    organizer_name: str
    organizer_url: str
    venue_name: str
    address: str
    city: str
    state_region: str
    country: str
    location: Point | None
    source_categories: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)


class EventClassification(BaseModel):
    career_fields: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    format: str = EventFormat.OTHER
    networking_relevant: bool = False
    networking_strength: float = Field(ge=0, le=1)
    likely_attendee_types: list[str] = Field(default_factory=list)
    experience_levels: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class EventClassificationInput:
    title: str
    description: str
    format_hint: str = ""
    organizer_name: str = ""
    source_categories: list[str] = field(default_factory=list)
