# Eventbrite

**Status:** explicit stub; not integrated

Official documentation: <https://www.eventbrite.com/platform/docs/>

- Authentication: OAuth/personal bearer token.
- Supported listing: events owned by an authenticated organization or venue,
  plus retrieval of a known event ID.
- Pagination: page-based, normally 50 records per page.
- Geographic discovery: no supported global public event-search endpoint.
- Limitation: Eventbrite shut down its public Event Search API in December 2019.
  Distribution partners can request broader access.

Legitimate MVP alternatives are direct organizer partnerships, organization IDs
for consenting partners, their public iCal feeds, or the distribution partner
program. Consumer-site/private endpoints are intentionally not used.
