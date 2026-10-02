from uuid import uuid4

from rest_framework import serializers

from events.domain.types import RawEvent
from events.ingestion.normalizer import EventNormalizer
from events.ingestion.pipeline import DuplicateEventError, EventIngestionPipeline
from events.models import Event, EventFormat
from events.services.geocoding import FixtureGeocodingService, GeocodingError


class EventCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300, trim_whitespace=True)
    description = serializers.CharField(required=False, allow_blank=True)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    timezone = serializers.CharField(max_length=64, default="America/Denver")
    format = serializers.ChoiceField(choices=EventFormat.choices)
    organizer_name = serializers.CharField(
        max_length=200, required=False, allow_blank=True, trim_whitespace=True
    )
    organizer_url = serializers.URLField(required=False, allow_blank=True)
    venue_name = serializers.CharField(
        max_length=200, required=False, allow_blank=True, trim_whitespace=True
    )
    address = serializers.CharField(
        max_length=300, required=False, allow_blank=True, trim_whitespace=True
    )
    city = serializers.CharField(
        max_length=100, required=False, allow_blank=True, trim_whitespace=True
    )
    state_region = serializers.CharField(
        max_length=100, required=False, allow_blank=True, trim_whitespace=True
    )
    country = serializers.CharField(max_length=2, default="US")
    event_url = serializers.URLField(required=False, allow_blank=True, max_length=500)

    def validate_title(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Title must not be blank.")
        return value

    def validate(self, attrs):
        start_time = attrs["start_time"]
        end_time = attrs.get("end_time")
        if end_time and end_time < start_time:
            raise serializers.ValidationError(
                {"end_time": "End time cannot be before start time."}
            )

        if attrs["format"] in (EventFormat.IN_PERSON, EventFormat.HYBRID):
            errors = {}
            if not attrs.get("city"):
                errors["city"] = "City is required for in-person and hybrid events."
            if not attrs.get("state_region"):
                errors["state_region"] = (
                    "State or region is required for in-person and hybrid events."
                )
            if not attrs.get("venue_name") and not attrs.get("address"):
                errors["venue_name"] = "Provide a venue name or street address."
            if errors:
                raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data) -> Event:
        city = validated_data.get("city", "")
        state_region = validated_data.get("state_region", "")
        point = None
        if city:
            geocoder = FixtureGeocodingService()
            try:
                point = geocoder.geocode(", ".join(filter(None, (city, state_region))))
            except GeocodingError:
                try:
                    point = geocoder.geocode(city)
                except GeocodingError:
                    # Unknown places remain nullable until a production geocoder is configured.
                    pass

        raw = RawEvent(
            provider="user_submitted",
            external_id=str(uuid4()),
            source_url=validated_data.get("event_url", ""),
            title=validated_data["title"],
            description=validated_data.get("description", ""),
            start_time=validated_data["start_time"],
            end_time=validated_data.get("end_time"),
            timezone=validated_data.get("timezone", "America/Denver"),
            format_hint=validated_data["format"],
            organizer_name=validated_data.get("organizer_name", ""),
            organizer_url=validated_data.get("organizer_url", ""),
            venue_name=validated_data.get("venue_name", ""),
            address=validated_data.get("address", ""),
            city=city,
            state_region=state_region,
            country=validated_data.get("country", "US"),
            latitude=point.y if point else None,
            longitude=point.x if point else None,
            raw_data={"submission_type": "public_form"},
        )
        normalized = EventNormalizer().normalize(raw)
        try:
            event, _result = EventIngestionPipeline().persist(
                normalized, reject_duplicates=True
            )
        except DuplicateEventError as exc:
            raise serializers.ValidationError(
                {"non_field_errors": [str(exc)]}
            ) from exc
        return event


class EventCreatedSerializer(serializers.ModelSerializer):
    event_url = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "description",
            "start_time",
            "end_time",
            "timezone",
            "format",
            "organizer_name",
            "organizer_url",
            "venue_name",
            "address",
            "city",
            "state_region",
            "country",
            "event_url",
            "source",
        )

    def get_event_url(self, event: Event) -> str:
        source = event.source_records.first()
        return source.source_url if source else ""

    def get_source(self, event: Event) -> str:
        source = event.source_records.first()
        return source.provider if source else ""


class EventSearchQuerySerializer(serializers.Serializer):
    career = serializers.CharField(max_length=120)
    location = serializers.CharField(max_length=200)
    radius_miles = serializers.FloatField(min_value=1, max_value=250, default=50)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    formats = serializers.ListField(
        child=serializers.ChoiceField(choices=EventFormat.choices),
        required=False,
        allow_empty=False,
    )

    def validate(self, attrs):
        if (
            attrs.get("start_date")
            and attrs.get("end_date")
            and attrs["start_date"] > attrs["end_date"]
        ):
            raise serializers.ValidationError("start_date must not be after end_date")
        return attrs


class EventResultSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="event.id")
    title = serializers.CharField(source="event.title")
    description = serializers.CharField(source="event.description")
    start_time = serializers.DateTimeField(source="event.start_time")
    end_time = serializers.DateTimeField(source="event.end_time", allow_null=True)
    timezone = serializers.CharField(source="event.timezone")
    format = serializers.CharField(source="event.format")
    venue = serializers.CharField(source="event.venue_name")
    city = serializers.CharField(source="event.city")
    state = serializers.CharField(source="event.state_region")
    organizer_name = serializers.CharField(source="event.organizer_name")
    career_fields = serializers.SerializerMethodField()
    topic_tags = serializers.ListField(source="event.topic_tags")
    likely_attendees = serializers.ListField(source="event.likely_attendee_types")
    networking_strength = serializers.FloatField(source="event.networking_strength")
    distance_miles = serializers.FloatField(allow_null=True)
    match_score = serializers.FloatField()
    score_breakdown = serializers.DictField()
    match_explanation = serializers.CharField()
    source_url = serializers.URLField(allow_blank=True)
    source_provider = serializers.CharField()

    def get_career_fields(self, value) -> list[str]:
        return [field.slug for field in value["event"].career_fields.all()]


class EventSearchResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    events = EventResultSerializer(many=True)
