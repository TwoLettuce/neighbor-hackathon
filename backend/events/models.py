from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class EventFormat(models.TextChoices):
    IN_PERSON = "IN_PERSON", "In person"
    HYBRID = "HYBRID", "Hybrid"
    LIVE_VIRTUAL = "LIVE_VIRTUAL", "Live virtual"
    WEBINAR = "WEBINAR", "Webinar"
    ASYNCHRONOUS = "ASYNCHRONOUS", "Asynchronous"
    OTHER = "OTHER", "Other"


class CareerField(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=120)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    keywords = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Event(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default="America/Denver")
    format = models.CharField(max_length=20, choices=EventFormat.choices, default=EventFormat.OTHER)

    organizer_name = models.CharField(max_length=200, blank=True)
    organizer_url = models.URLField(blank=True)
    venue_name = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, default="US")
    location = models.PointField(geography=True, null=True, blank=True, spatial_index=True)

    career_fields = models.ManyToManyField(CareerField, blank=True, related_name="events")
    topic_tags = models.JSONField(default=list, blank=True)
    likely_attendee_types = models.JSONField(default=list, blank=True)
    experience_levels = models.JSONField(default=list, blank=True)
    networking_relevant = models.BooleanField(default=False)
    networking_strength = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    quality_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()

    class Meta:
        ordering = ["start_time"]
        indexes = [
            models.Index(fields=["format", "start_time"]),
            models.Index(fields=["networking_relevant", "start_time"]),
        ]

    def __str__(self) -> str:
        return self.title


class EventSourceRecord(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="source_records")
    provider = models.CharField(max_length=50)
    external_id = models.CharField(max_length=255)
    source_url = models.URLField(max_length=500)
    raw_data = models.JSONField(default=dict)
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_id"], name="unique_provider_external_event"
            )
        ]
        indexes = [models.Index(fields=["provider", "external_id"])]

    def __str__(self) -> str:
        return f"{self.provider}: {self.external_id}"
