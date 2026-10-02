from abc import ABC, abstractmethod

from events.domain.types import RawEvent


class ProviderUnavailableError(RuntimeError):
    pass


class EventProvider(ABC):
    name: str
    audience: str = "public"

    @abstractmethod
    def fetch_events(self) -> list[RawEvent]:
        """Fetch and translate provider records into domain-level raw events."""


class RestrictedProviderStub(EventProvider):
    reason: str

    def fetch_events(self) -> list[RawEvent]:
        raise ProviderUnavailableError(self.reason)


class MeetupProvider(RestrictedProviderStub):
    name = "meetup"
    reason = "Meetup API access requires approved OAuth access; configure a real adapter first."


class EventbriteProvider(RestrictedProviderStub):
    name = "eventbrite"
    reason = "Eventbrite does not provide unrestricted global public discovery via its API."


class LumaProvider(RestrictedProviderStub):
    name = "luma"
    reason = "Luma API access is organizer-oriented and is not a global public discovery API."


class HandshakeProvider(RestrictedProviderStub):
    name = "handshake"
    audience = "personalized"
    reason = "Handshake is a later authenticated university/user integration."
