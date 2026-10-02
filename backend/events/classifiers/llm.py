from collections.abc import Callable

from events.classifiers.base import EventClassifier
from events.domain.types import EventClassification, EventClassificationInput


class LLMEventClassifier(EventClassifier):
    """Optional adapter around a caller that returns structured JSON.

    A deployment can inject an OpenAI-, Anthropic-, or other compatible caller.
    No vendor SDK or network call is required by the core application.
    """

    def __init__(self, structured_caller: Callable[[dict[str, str]], dict]) -> None:
        self.structured_caller = structured_caller

    def classify(self, event: EventClassificationInput) -> EventClassification:
        payload = self.structured_caller(
            {
                "title": event.title,
                "description": event.description,
                "format_hint": event.format_hint,
                "organizer_name": event.organizer_name,
            }
        )
        return EventClassification.model_validate(payload)
