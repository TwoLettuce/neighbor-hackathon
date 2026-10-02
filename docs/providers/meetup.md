# Meetup

**Status:** explicit stub; not integrated

Official documentation: <https://www.meetup.com/graphql/>

- Authentication: OAuth 2 bearer token; official GraphQL endpoint is
  `https://api.meetup.com/gql-ext`.
- Discovery: the documented `eventSearch` workflow is oriented to a customer's
  Pro Network, not unrestricted global public discovery.
- Pagination: GraphQL cursor pagination.
- Geographic search: schema/access dependent; not available here as a supported
  global-ingestion contract.
- Rate limits: account/contract dependent; handle GraphQL errors and backoff.
- Limitation: Meetup's consumer website uses other internal endpoints, but this
  project will not depend on undocumented reverse-engineered APIs.

A real adapter becomes appropriate after approved OAuth/Pro access or a written
distribution agreement. The current command fails clearly rather than returning
fabricated data.
