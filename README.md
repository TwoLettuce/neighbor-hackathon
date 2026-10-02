# Neighbor

Neighbor finds upcoming events where job seekers can build useful professional relationships. It ingests events ahead of time, normalizes and classifies them, stores them in PostGIS, then ranks local and interactive virtual events by career fit and networking potential.

## Stack

- Next.js 16, React, TypeScript, Tailwind CSS
- Django 5, Django REST Framework, GeoDjango
- PostgreSQL 16 + PostGIS
- pytest and pytest-django

## Local setup

Prerequisites: Python 3.12+, Node 20.19+ or 22.13+, Docker Desktop, and GeoDjango native libraries. On macOS install the latter with `brew install gdal geos`.

```bash
cp .env.example .env
docker compose up -d db

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py seed_events
python backend/manage.py runserver
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>. Search for `Software Engineer`, `Provo, UT`, and `50 miles`. Django Admin is at <http://localhost:8000/admin/> and browsable OpenAPI documentation is at <http://localhost:8000/api/docs/>.

## Ingestion

The default credential-free command refreshes 24 realistic rolling Utah fixtures and is idempotent:

```bash
python backend/manage.py ingest_events
```

A real public iCal feed can be imported with:

```bash
python backend/manage.py ingest_events --provider ical --feed-url https://example.org/events.ics
```

Only trusted, operator-configured feed URLs should be used. Meetup, Eventbrite, Luma, and Handshake commands are explicit stubs because their supported APIs do not provide unrestricted global public discovery. See `docs/providers/` for current capabilities and legitimate integration paths.

## Verification

```bash
pytest backend/tests
ruff check backend
cd frontend
npm run lint
npm run typecheck
npm run build
```

The integration tests require the PostGIS service. Ranking, classification, deduplication, normalization, ingestion idempotency, API behavior, and geographic radius filtering are covered.

## Project layout

- `backend/events/providers/`: provider contracts and adapters
- `backend/events/ingestion/`: normalization and persistence pipeline
- `backend/events/classifiers/`: rule-based and optional structured-LLM interfaces
- `backend/events/deduplication/`: deterministic duplicate scoring
- `backend/events/ranking/`: explainable ranking components
- `backend/events/services/`: taxonomy, geocoding, and search orchestration
- `frontend/`: search and ranked-results UI
- `docs/`: architecture, ranking, and provider constraints

## Current limitations

Development geocoding recognizes Provo, Orem, Lehi, Draper, South Jordan, and Salt Lake City. iCal location strings are not yet geocoded automatically. There is no user authentication or personalization. Seed source URLs intentionally use `example.com`, and provider stubs require approved partner access before implementation.
