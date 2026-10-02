from abc import ABC, abstractmethod

from events.domain.types import EventClassification, EventClassificationInput


class EventClassifier(ABC):
    @abstractmethod
    def classify(self, event: EventClassificationInput) -> EventClassification:
        """Return provider-independent structured classification."""
