# Architecture

Neighbor separates collection from search:

```text
Public/provider feeds → provider adapters → RawEvent → normalization
    → deterministic deduplication → classification → PostgreSQL/PostGIS
    → search + ranking service → Django REST API → Next.js
```

Search never calls external event APIs. Provider objects translate third-party
records into `RawEvent`; the ingestion pipeline owns normalization, enrichment,
deduplication, and persistence. `EventSourceRecord` preserves source identity and
raw payloads while multiple records may point to one canonical `Event`.

## Boundaries

- `providers/`: authentication, pagination, rate limiting, provider translation.
- `ingestion/`: provider-independent orchestration and persistence.
- `classifiers/`: replaceable rule and optional structured-LLM classifiers.
- `deduplication/`: deterministic, inspectable matching.
- `services/search.py`: geographic retrieval and search workflow.
- `ranking/`: pure scoring components and deterministic explanations.
- DRF views and serializers: transport and validation only.

Public ingestion populates a shared event database. Future personalized sources
such as Handshake should be connected per user and merged into results after
authorization; they must not become a requirement for public search.

## Scheduling

The management command is intentionally synchronous for the MVP. Run it from
cron, a cloud scheduler, or CI. A later Celery task can invoke the same
`EventIngestionPipeline` without changing provider or domain code.
