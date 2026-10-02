import re

from events.classifiers.base import EventClassifier
from events.domain.types import EventClassification, EventClassificationInput
from events.models import EventFormat
from events.services.taxonomy import CAREER_TAXONOMY

TOPICS = {
    "javascript": ("javascript", "typescript", "react", "node.js"),
    "python": ("python", "django", "flask"),
    "rust": ("rust",),
    "linux": ("linux", "open source"),
    "cloud": ("cloud", "aws", "azure", "kubernetes", "devops"),
    "cybersecurity": ("cybersecurity", "security", "infosec", "owasp"),
    "ai": ("artificial intelligence", "machine learning", " ai ", "llm"),
    "career_development": ("career fair", "recruiter", "hiring", "job seeker"),
}


class RuleBasedEventClassifier(EventClassifier):
    def classify(self, event: EventClassificationInput) -> EventClassification:
        text = (
            f" {event.title} {event.description} {event.organizer_name} "
            f"{' '.join(event.source_categories)} "
        ).lower()

        careers = [
            slug
            for slug, definition in CAREER_TAXONOMY.items()
            if any(keyword in text for keyword in definition.keywords)
        ]
        inferred_topics = [
            topic for topic, keywords in TOPICS.items() if any(word in text for word in keywords)
        ]
        source_topics = [
            re.sub(r"[^a-z0-9]+", "_", category.lower()).strip("_")
            for category in event.source_categories
            if category.strip()
        ]
        topics = list(dict.fromkeys(inferred_topics + source_topics))
        event_format = self._format(text, event.format_hint)
        strength = self._networking_strength(text, event_format)
        attendee_types = self._attendees(careers, text)

        return EventClassification(
            career_fields=careers,
            topics=topics,
            format=event_format,
            networking_relevant=strength >= 0.4,
            networking_strength=strength,
            likely_attendee_types=attendee_types,
            experience_levels=["students", "early career"]
            if "career fair" in text or "student" in text
            else ["all levels"],
        )

    @staticmethod
    def _format(text: str, hint: str) -> str:
        normalized_hint = hint.upper().replace(" ", "_")
        if normalized_hint in EventFormat.values:
            return normalized_hint
        if any(term in text for term in ("prerecorded", "on demand", "self-paced")):
            return EventFormat.ASYNCHRONOUS
        if "webinar" in text and not any(term in text for term in ("q&a", "breakout")):
            return EventFormat.WEBINAR
        if "hybrid" in text:
            return EventFormat.HYBRID
        if any(term in text for term in ("virtual", "online", "zoom")):
            return EventFormat.LIVE_VIRTUAL
        return EventFormat.IN_PERSON

    @staticmethod
    def _networking_strength(text: str, event_format: str) -> float:
        score = {
            EventFormat.IN_PERSON: 0.55,
            EventFormat.HYBRID: 0.5,
            EventFormat.LIVE_VIRTUAL: 0.35,
            EventFormat.WEBINAR: 0.12,
            EventFormat.ASYNCHRONOUS: 0.02,
            EventFormat.OTHER: 0.25,
        }[event_format]
        positives = {
            "meetup": 0.2,
            "networking": 0.2,
            "career fair": 0.2,
            "mixer": 0.18,
            "workshop": 0.1,
            "discussion": 0.1,
            "q&a": 0.08,
            "recruiter": 0.12,
        }
        negatives = {
            "prerecorded": -0.5,
            "on demand": -0.4,
            "lecture only": -0.2,
            "concert": -0.45,
            "music": -0.35,
            "sports": -0.45,
            "arts & theatre": -0.4,
            "arts and theatre": -0.4,
            "theater performance": -0.4,
            "theatre performance": -0.4,
        }
        score += sum(value for term, value in positives.items() if term in text)
        score += sum(value for term, value in negatives.items() if term in text)
        return round(max(0.0, min(1.0, score)), 2)

    @staticmethod
    def _attendees(careers: list[str], text: str) -> list[str]:
        labels = {
            "software_engineering": "software engineers",
            "frontend_engineering": "web developers",
            "backend_engineering": "backend engineers",
            "cloud_engineering": "cloud and DevOps engineers",
            "cybersecurity": "security professionals",
            "machine_learning": "AI and data practitioners",
            "marketing": "marketing professionals",
            "healthcare": "healthcare professionals",
        }
        attendees = [labels[slug] for slug in careers if slug in labels]
        if "recruiter" in text or "career fair" in text:
            attendees.append("recruiters and employers")
        return list(dict.fromkeys(attendees)) or ["professionals and community members"]
