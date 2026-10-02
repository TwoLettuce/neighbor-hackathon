import os
import unittest
from unittest.mock import MagicMock, patch

from events.domain.types import RawEvent
from events.providers.base import ProviderUnavailableError
from events.providers.ticketmaster import TicketmasterProvider


class TicketmasterProviderTestCase(unittest.TestCase):
    def test_missing_api_key_raises_provider_unavailable_error(self):
        with patch.dict(os.environ, {}, clear=True):
            provider = TicketmasterProvider(api_key=None)
            with self.assertRaises(ProviderUnavailableError) as ctx:
                provider.fetch_events()
            self.assertIn("Ticketmaster API key is not configured", str(ctx.exception))

    @patch("events.providers.ticketmaster.requests.get")
    def test_fetch_events_success_and_parsing(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "_embedded": {
                "events": [
                    {
                        "id": "vvG1YZ94v6_tP7",
                        "name": "Tech Leaders Summit & Networking Mixer",
                        "url": "https://www.ticketmaster.com/event/vvG1YZ94v6_tP7",
                        "dates": {
                            "start": {
                                "localDate": "2026-11-15",
                                "localTime": "18:00:00",
                                "dateTime": "2026-11-16T01:00:00Z",
                            },
                            "timezone": "America/Denver",
                        },
                        "info": "Annual leadership mixer for developers and engineers.",
                        "classifications": [
                            {
                                "segment": {"name": "Miscellaneous"},
                                "genre": {"name": "Networking"},
                            }
                        ],
                        "_embedded": {
                            "venues": [
                                {
                                    "name": "Salt Palace Convention Center",
                                    "address": {"line1": "100 S West Temple"},
                                    "city": {"name": "Salt Lake City"},
                                    "state": {"stateCode": "UT", "name": "Utah"},
                                    "country": {"countryCode": "US"},
                                    "location": {
                                        "latitude": "40.7681",
                                        "longitude": "-111.8967",
                                    },
                                }
                            ]
                        },
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        provider = TicketmasterProvider(api_key="test-api-key", city="Salt Lake City", state_code="UT")
        events = provider.fetch_events()

        self.assertEqual(len(events), 1)
        raw = events[0]
        self.assertIsInstance(raw, RawEvent)
        self.assertEqual(raw.provider, "ticketmaster")
        self.assertEqual(raw.external_id, "vvG1YZ94v6_tP7")
        self.assertEqual(raw.title, "Tech Leaders Summit & Networking Mixer")
        self.assertEqual(raw.city, "Salt Lake City")
        self.assertEqual(raw.state_region, "UT")
        self.assertEqual(raw.country, "US")
        self.assertAlmostEqual(raw.latitude, 40.7681)
        self.assertAlmostEqual(raw.longitude, -111.8967)
        self.assertIn("Networking", raw.description)
        self.assertEqual(raw.venue_name, "Salt Palace Convention Center")


if __name__ == "__main__":
    unittest.main()
