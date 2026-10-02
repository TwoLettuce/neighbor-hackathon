from rest_framework import serializers

from events.models import EventFormat


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
    source_url = serializers.URLField()
    source_provider = serializers.CharField()

    def get_career_fields(self, value) -> list[str]:
        return [field.slug for field in value["event"].career_fields.all()]


class EventSearchResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    events = EventResultSerializer(many=True)
