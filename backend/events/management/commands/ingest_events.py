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


class Command(BaseCommand):
    help = "Ingest events idempotently through a provider adapter"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--provider",
            default="seed",
            choices=["seed", "ical", "ticketmaster", "meetup", "eventbrite", "luma", "handshake"],
        )
        parser.add_argument(
            "--feed-url",
            help="Preconfigured public HTTP(S) iCal URL (required for --provider ical)",
        )
        parser.add_argument(
            "--city",
            help="City filter (for Ticketmaster provider)",
        )
        parser.add_argument(
            "--state",
            help="State code filter e.g. UT (for Ticketmaster provider)",
        )
        parser.add_argument(
            "--keyword",
            help="Keyword query filter (for Ticketmaster provider)",
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
            provider = TicketmasterProvider(
                city=options.get("city"),
                state_code=options.get("state"),
                keyword=options.get("keyword"),
            )
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

        self.stdout.write(f"{provider.name}:")
        self.stdout.write(f"  {stats.retrieved} records retrieved")
        self.stdout.write(f"  {stats.normalized} normalized")
        self.stdout.write(f"  {stats.matched} matched existing events")
        self.stdout.write(f"  {stats.created} new events")
        self.stdout.write(f"  {stats.updated} updated")
        self.stdout.write(f"  {stats.failed} failed")
