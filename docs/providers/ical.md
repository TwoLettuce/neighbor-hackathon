# Public iCalendar feeds

**Status:** real implementation (`ICalProvider`)

Many universities, associations, and company event calendars publish standard
iCal feeds. A configured feed URL is fetched server-side and parsed into
provider-independent `RawEvent` records.

- Authentication: usually none; feed-specific credentials are possible later.
- Discovery: only events from feeds explicitly configured by an operator.
- Pagination: not part of iCalendar; the complete feed is returned.
- Geographic search: none; locations are normalized/geocoded after retrieval.
- Rate limits: publisher-specific. Schedule conservatively and cache in Postgres.
- Endpoint: operator-supplied HTTPS feed URL.

Run `python manage.py ingest_events --provider ical --feed-url <trusted-url>`.
The URL is a management-command/operator input, never an unauthenticated user
input. Feed location geocoding is a future enhancement.
