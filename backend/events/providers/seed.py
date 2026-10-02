from datetime import timedelta
from typing import Any

from django.utils import timezone

from events.domain.types import RawEvent
from events.models import EventFormat
from events.providers.base import EventProvider


class SeedEventProvider(EventProvider):
    """Deterministic demo catalog; dates roll forward so the app remains demonstrable."""

    name = "seed"
    LOCATIONS = {
        "Provo": (40.2338, -111.6585),
        "Orem": (40.2969, -111.6946),
        "Lehi": (40.3916, -111.8508),
        "Draper": (40.5247, -111.8638),
        "South Jordan": (40.5622, -111.9297),
        "Salt Lake City": (40.7608, -111.8910),
    }
    CATALOG: list[dict[str, Any]] = [
        {
            "title": "UtahJS Lehi Developer Meetup",
            "city": "Lehi",
            "days": 6,
            "organizer": "UtahJS",
            "venue": "Kiln Lehi",
            "description": "JavaScript and TypeScript lightning talks, community discussion, and dedicated networking time.",
        },
        {
            "title": "Python Utah Monthly Meetup",
            "city": "Salt Lake City",
            "days": 9,
            "organizer": "Python Utah",
            "venue": "Church & State",
            "description": "Python developers share projects, Q&A, and meet peers over refreshments.",
        },
        {
            "title": "Rust Wasatch Community Night",
            "city": "Provo",
            "days": 12,
            "organizer": "Rust Wasatch",
            "venue": "Provo Library",
            "description": "Hands-on Rust programming demos followed by an open developer mixer.",
        },
        {
            "title": "Utah Open Source & Linux User Group",
            "city": "Orem",
            "days": 14,
            "organizer": "UTOS",
            "venue": "UVU Business Resource Center",
            "description": "Linux, infrastructure, and open source discussion with community networking.",
        },
        {
            "title": "OWASP Utah Cybersecurity Meetup",
            "city": "Draper",
            "days": 17,
            "organizer": "OWASP Utah",
            "venue": "Proofpoint",
            "description": "Application security talk, Q&A, and networking for cybersecurity professionals.",
        },
        {
            "title": "Silicon Slopes AI Practitioners Meetup",
            "city": "Lehi",
            "days": 20,
            "organizer": "Silicon Slopes AI",
            "venue": "Adobe Lehi",
            "description": "Machine learning and LLM case studies plus facilitated attendee introductions.",
        },
        {
            "title": "BYU STEM Career Fair",
            "city": "Provo",
            "days": 23,
            "organizer": "BYU Career Services",
            "venue": "Wilkinson Student Center",
            "description": "Meet recruiters and engineering teams hiring software, data, and technology roles.",
        },
        {
            "title": "UVU Computing & Engineering Career Fair",
            "city": "Orem",
            "days": 27,
            "organizer": "UVU Career Services",
            "venue": "UVU Grande Ballroom",
            "description": "Interactive university career fair with technical employers and recruiters.",
        },
        {
            "title": "Cloud Native Utah: Kubernetes Workshop",
            "city": "South Jordan",
            "days": 30,
            "organizer": "Cloud Native Utah",
            "venue": "Lucid Software",
            "description": "Small-group Kubernetes workshop, pair exercises, discussion, and DevOps networking.",
        },
        {
            "title": "Engineering Open House at Entrata",
            "city": "Lehi",
            "days": 33,
            "organizer": "Entrata Engineering",
            "venue": "Entrata HQ",
            "description": "Company-hosted engineering demos, office tour, hiring team Q&A, and networking.",
        },
        {
            "title": "Salt Lake DevOps Days",
            "city": "Salt Lake City",
            "days": 38,
            "organizer": "DevOps Utah",
            "venue": "Salt Palace",
            "description": "Conference for cloud and reliability engineers with open spaces and networking reception.",
            "format": EventFormat.HYBRID,
        },
        {
            "title": "Women Who Code Utah Community Social",
            "city": "Draper",
            "days": 41,
            "organizer": "Utah Tech Women",
            "venue": "Divvy",
            "description": "Inclusive social for software engineers, technical mentors, and people entering tech.",
        },
        {
            "title": "Utah Product + Engineering Mixer",
            "city": "Provo",
            "days": 45,
            "organizer": "Product Utah",
            "venue": "The Startup Building",
            "description": "Structured networking for product managers, designers, founders, and software engineers.",
        },
        {
            "title": "Startup Founders Friday Mixer",
            "city": "Lehi",
            "days": 4,
            "organizer": "Point of the Mountain Chamber",
            "venue": "Thanksgiving Point",
            "description": "Open networking mixer for founders, operators, investors, and startup employees.",
        },
        {
            "title": "Utah Marketing Leaders Roundtable",
            "city": "Draper",
            "days": 11,
            "organizer": "Utah AMA",
            "venue": "Draper Peaks",
            "description": "Interactive roundtable and networking for brand, growth, and marketing professionals.",
        },
        {
            "title": "Healthcare Careers Networking Night",
            "city": "Salt Lake City",
            "days": 18,
            "organizer": "Utah Health Association",
            "venue": "University of Utah",
            "description": "Healthcare professionals, students, and clinical employers connect in person.",
        },
        {
            "title": "Wasatch Finance Professionals Breakfast",
            "city": "South Jordan",
            "days": 25,
            "organizer": "Wasatch Finance Council",
            "venue": "Embassy Suites",
            "description": "Breakfast networking for finance, accounting, and banking professionals.",
        },
        {
            "title": "Modern Python Architecture Webinar",
            "city": "Provo",
            "days": 8,
            "organizer": "Code Learning Online",
            "venue": "Online",
            "description": "Large lecture-only webinar with no attendee interaction.",
            "format": EventFormat.WEBINAR,
        },
        {
            "title": "Learn React On Demand",
            "city": "Provo",
            "days": 2,
            "organizer": "Video Academy",
            "venue": "Online",
            "description": "Prerecorded self-paced React tutorial available on demand.",
            "format": EventFormat.ASYNCHRONOUS,
        },
        {
            "title": "National Virtual Technology Career Fair",
            "city": "Provo",
            "days": 16,
            "organizer": "Career Connect",
            "venue": "Online",
            "description": "Live virtual career fair with recruiter booths, chat, and one-to-one conversations.",
            "format": EventFormat.LIVE_VIRTUAL,
        },
        {
            "title": "Interactive Systems Design Office Hours",
            "city": "Provo",
            "days": 21,
            "organizer": "Architecture Guild",
            "venue": "Online",
            "description": "Live technical event with small breakout rooms, Q&A, and peer networking.",
            "format": EventFormat.LIVE_VIRTUAL,
        },
        {
            "title": "Salt Lake UX Design Critique",
            "city": "Salt Lake City",
            "days": 28,
            "organizer": "SLC Design Community",
            "venue": "Impact Hub",
            "description": "Collaborative UX portfolio critique and networking for product designers.",
        },
        {
            "title": "Operations & Supply Chain Exchange",
            "city": "Orem",
            "days": 35,
            "organizer": "Utah Operations Network",
            "venue": "UVU",
            "description": "Peer discussions and professional networking for operations leaders.",
        },
        {
            "title": "Silicon Slopes General Business Connect",
            "city": "Lehi",
            "days": 43,
            "organizer": "Silicon Slopes",
            "venue": "Kiln",
            "description": "Broad business networking for sales, founders, marketers, and operators.",
        },
    ]

    def fetch_events(self) -> list[RawEvent]:
        base = timezone.now().replace(hour=18, minute=0, second=0, microsecond=0)
        events: list[RawEvent] = []
        for index, item in enumerate(self.CATALOG, start=1):
            latitude, longitude = self.LOCATIONS[item["city"]]
            start = base + timedelta(days=item["days"])
            events.append(
                RawEvent(
                    provider=self.name,
                    external_id=f"seed-{index}",
                    source_url=f"https://example.com/seed-events/{index}",
                    title=item["title"],
                    description=item["description"],
                    start_time=start,
                    end_time=start + timedelta(hours=2),
                    format_hint=item.get("format", EventFormat.IN_PERSON),
                    organizer_name=item["organizer"],
                    venue_name=item["venue"],
                    address=f"{100 + index} Demo Street",
                    city=item["city"],
                    state_region="UT",
                    latitude=latitude,
                    longitude=longitude,
                    raw_data={"fixture": True, "catalog_id": index},
                )
            )
        return events
