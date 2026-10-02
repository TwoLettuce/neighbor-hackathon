from django.contrib import admin

from events.models import CareerField, Event, EventSourceRecord


class EventSourceInline(admin.TabularInline):
    model = EventSourceRecord
    extra = 0
    readonly_fields = ("first_seen_at", "last_seen_at")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "start_time",
        "city",
        "format",
        "status",
        "networking_relevant",
        "networking_strength",
        "last_seen_at",
    )
    list_filter = ("status", "format", "networking_relevant", "city", "career_fields")
    search_fields = ("title", "description", "organizer_name", "venue_name")
    readonly_fields = ("created_at", "updated_at", "first_seen_at", "last_seen_at")
    filter_horizontal = ("career_fields",)
    inlines = (EventSourceInline,)


@admin.register(EventSourceRecord)
class EventSourceRecordAdmin(admin.ModelAdmin):
    list_display = ("provider", "external_id", "event", "last_seen_at")
    list_filter = ("provider",)
    search_fields = ("external_id", "event__title", "source_url")
    readonly_fields = ("first_seen_at", "last_seen_at")


@admin.register(CareerField)
class CareerFieldAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent")
    search_fields = ("name", "slug")
