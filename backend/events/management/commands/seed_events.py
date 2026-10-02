from events.management.commands.ingest_events import Command as IngestCommand


class Command(IngestCommand):
    help = "Load or refresh the realistic Utah demo event catalog"

    def handle(self, *args, **options) -> None:
        options["provider"] = "seed"
        options["feed_url"] = None
        super().handle(*args, **options)
