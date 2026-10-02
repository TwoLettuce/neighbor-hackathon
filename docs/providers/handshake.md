# Handshake

**Status:** personalized/institutional stub; not part of public ingestion

Official documentation:
<https://support.joinhandshake.com/hc/en-us/articles/31061076506391-Getting-Started-with-EDU-API>

- Authentication: institution-issued `x-api-key`.
- Access: read-only, institution-scoped EDU API; access is gated to Career
  Services partners through a Handshake relationship manager.
- Event endpoints: `/events`, `/career_fairs`, related attendance and employer
  engagement resources.
- Pagination: `page_size`, sorting, and delta fetching via `updated_since`.
- Geographic search: not a global public geo-discovery API.
- Limitation: records and permissions belong to a participating institution.

Handshake should be a later account/institution connection. Authorized records
can augment public results for that user but must not enter a shared public
catalog unless their terms and visibility permit it.
