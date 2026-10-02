# Luma

**Status:** explicit stub; not integrated

Official documentation: <https://docs.luma.com/reference/getting-started-with-your-api>

- Authentication: calendar API key in `x-luma-api-key` or OAuth; API keys
  require Luma Plus and are calendar-scoped.
- Discovery: official API lists events managed/viewed by an authorized calendar
  or organization. It is not unrestricted global public discovery.
- Endpoints: `/v1/calendars/events/list`, `/v1/organizations/events/list`, and
  `/v1/events/get`.
- Pagination: cursor-based.
- Rate limits: 200 requests/minute per calendar key or OAuth token; 500/minute
  per organization key. Respect `429` with backoff.
- Geographic search: no official global geo-search contract.

Integrate calendars whose organizers authorize Job'n'Weave, or consume an
organizer's public iCal feed. Undocumented consumer discovery endpoints are not
used as a production dependency.
