from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from events.ingestion.pipeline import EventIngestionPipeline
from events.providers.base import (
    EventbriteProvider,
    HandshakeProvider,
    LumaProvider,
    MeetupProvider,
    ProviderUnavailableError,
)
from events.providers.ical import ICalProvider
from events.providers.seed import SeedEventProvider
from events.providers.ticketmaster import TicketmasterProvider
from events.services.geocoding import FixtureGeocodingService, GeocodingError


class Command(BaseCommand):
    help = "Ingest events idempotently through a provider adapter"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--provider",
            default="seed",
            choices=[
                "seed",
                "ical",
                "ticketmaster",
                "meetup",
                "eventbrite",
                "luma",
                "handshake",
            ],
        )
        parser.add_argument(
            "--feed-url",
            help="Preconfigured public HTTP(S) iCal URL (required for --provider ical)",
        )
        parser.add_argument(
            "--location",
            help="Location to geocode (required for --provider ticketmaster)",
        )
        parser.add_argument(
            "--radius",
            type=int,
            default=50,
            help="Ticketmaster search radius in miles (default: 50)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Upcoming Ticketmaster date window (default: 90)",
        )
        parser.add_argument(
            "--max-pages",
            type=int,
            default=10,
            help="Maximum Ticketmaster API pages, bounded by 1,000 results (default: 10)",
        )
        parser.add_argument(
            "--keyword",
            help="Optional Ticketmaster keyword filter",
        )

    def handle(self, *args, **options) -> None:
        provider_name = options["provider"]
        if provider_name == "seed":
            provider = SeedEventProvider()
        elif provider_name == "ical":
            if not options["feed_url"]:
                raise CommandError("--feed-url is required for the iCal provider")
            provider = ICalProvider(options["feed_url"])
        elif provider_name == "ticketmaster":
            if not options["location"]:
                raise CommandError("--location is required for the Ticketmaster provider")
            if not settings.TICKETMASTER_API_KEY:
                raise CommandError("TICKETMASTER_API_KEY is not configured")
            try:
                origin = FixtureGeocodingService().geocode(options["location"])
                provider = TicketmasterProvider(
                    api_key=settings.TICKETMASTER_API_KEY,
                    latitude=origin.y,
                    longitude=origin.x,
                    radius_miles=options["radius"],
                    days=options["days"],
                    keyword=options["keyword"],
                    max_pages=options["max_pages"],
                    base_url=settings.TICKETMASTER_API_BASE_URL,
                )
            except (GeocodingError, ValueError) as exc:
                raise CommandError(str(exc)) from exc
        else:
            provider = {
                "meetup": MeetupProvider,
                "eventbrite": EventbriteProvider,
                "luma": LumaProvider,
                "handshake": HandshakeProvider,
            }[provider_name]()

        try:
            stats = EventIngestionPipeline().ingest(provider)
        except ProviderUnavailableError as exc:
            raise CommandError(str(exc)) from exc

        if isinstance(provider, TicketmasterProvider):
            self.stdout.write("Ticketmaster ingestion")
            self.stdout.write("")
            self.stdout.write(f"Location: {options['location']}")
            self.stdout.write(f"Radius: {options['radius']:g} miles")
            self.stdout.write(f"Window: next {options['days']} days")
            if options["keyword"]:
                self.stdout.write(f"Keyword: {options['keyword']}")
            self.stdout.write("")
            self.stdout.write(f"Pages fetched: {provider.pages_fetched}")
            self.stdout.write(f"API records retrieved: {provider.records_retrieved}")
            self.stdout.write(f"Records normalized: {stats.normalized}")
            self.stdout.write(f"Records skipped: {provider.records_skipped + stats.failed}")
            self.stdout.write(f"New events: {stats.created}")
            self.stdout.write(f"Existing events updated: {stats.updated}")
            self.stdout.write(f"Duplicate matches: {stats.matched}")
            self.stdout.write(f"Errors: {stats.failed}")
            return

        self.stdout.write(f"{provider.name}:")
        self.stdout.write(f"  {stats.retrieved} records retrieved")
        self.stdout.write(f"  {stats.normalized} normalized")
        self.stdout.write(f"  {stats.matched} matched existing events")
        self.stdout.write(f"  {stats.created} new events")
        self.stdout.write(f"  {stats.updated} updated")
        self.stdout.write(f"  {stats.failed} failed")
