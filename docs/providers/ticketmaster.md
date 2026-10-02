# Ticketmaster Discovery API

**Status:** real implementation (`TicketmasterProvider`)

Neighbor uses Ticketmaster's official Discovery API v2 Event Search endpoint:
<https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/>.
Create an application in the Ticketmaster Developer Portal, then place its
consumer key in the server-side `.env` file:

```dotenv
TICKETMASTER_API_KEY=<your consumer key>
```

The key is sent only as the API's required `apikey` query parameter. It is not
sent to the frontend, printed by the management command, or stored with event
source data. Do not commit `.env`.

## Ingestion

```bash
python backend/manage.py ingest_events \
  --provider ticketmaster \
  --location "Provo, UT" \
  --radius 50 \
  --days 90
```

`--location` is resolved through Neighbor's existing geocoding service. The
resulting coordinates are encoded as a geohash and sent through `geoPoint`;
the deprecated Ticketmaster `latlong` parameter is not used. Radius values are
in miles, and searches default to `countryCode=US`.

The date window defaults to the next 90 days and is sent as UTC
`startDateTime` and `endDateTime` values. Results are requested in ascending
date order. An optional `--keyword "networking"` narrows Ticketmaster's search,
but the provider has no hardcoded profession or keyword list.

For a low-cost development request, add `--max-pages 1`. The default is 10
100-record pages. In every case, ingestion stops before Ticketmaster's
documented 1,000-result deep-paging boundary.

## Reliability and source behavior

- Requests use explicit connect/read timeouts and are paced to at most roughly
  two requests per second, below Ticketmaster's documented default limit.
- HTTP 429, transient 5xx responses, timeouts, and connection failures receive
  a small bounded retry with backoff. Authentication errors fail immediately.
- Malformed individual event records are skipped without aborting the page.
- Ticketmaster event IDs are stored as source external IDs, so repeated runs
  update the same `EventSourceRecord` and continue through Neighbor's existing
  cross-provider deduplication logic.
- Events with only a calendar date and no precise time are skipped because the
  current Neighbor model cannot represent an unknown event time without
  inventing one.

Ticketmaster is strong for concerts, sports, theater, and other ticketed public
events. It is not primarily a professional-event catalog, so many records will
correctly receive low networking relevance and remain absent from career search
results. This is expected; use optional keywords when an operator wants a
narrower import, and do not weaken classification to force entertainment events
into results.
