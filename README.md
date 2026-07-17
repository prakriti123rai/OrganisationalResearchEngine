# Organizational Reasoning Engine

ORE is the Organizational Reasoning Engine implementation defined by the frozen design documents.
The current implementation includes the project foundation, canonical data model, and seeded demo organization.

## Stack

- Frontend: Next.js App Router, React 19, TypeScript, Tailwind, shadcn-style UI primitives.
- Backend: FastAPI and Pydantic.
- Databases: PostgreSQL and Neo4j.
- Deployment: Docker Compose.

## Local Startup

Copy the environment template if you want to override defaults:

```bash
cp .env.example .env
```

Start the full foundation:

```bash
docker compose up --build
```

The frontend runs at `http://localhost:3000`.
The backend health endpoint runs at `http://localhost:8000/health`.
Neo4j Browser runs at `http://localhost:7474`.

## Demo Seed

Docker backend startup applies migrations and seeds the demo organization automatically.
For local backend development, run the same seed directly after applying migrations:

```bash
cd backend
alembic upgrade head
python -m app.seed.demo_organization
```

The seed is idempotent and uses the demo organization id `org-demo-apex`.

## Evidence API

Milestone 4 adds the evidence service API:

```bash
curl http://localhost:8000/organizations/org-demo-apex/evidence
curl http://localhost:8000/organizations/org-demo-apex/evidence/evidence-pr-checkout-482
```

Evidence can be listed, filtered, read by id, and created with canonical links to entities, relationships, signals, and assumptions.
Milestone 5 adds the organizational graph API:

```bash
curl http://localhost:8000/organizations/org-demo-apex/graph
curl -X POST http://localhost:8000/organizations/org-demo-apex/graph/sync
```

The graph can be read from canonical Postgres data and synced idempotently into Neo4j.
The frontend dashboard, evidence explorer, and graph view load the seeded organization through the backend APIs.
Milestone 6 adds deterministic reasoning context builder APIs:

```bash
curl http://localhost:8000/organizations/org-demo-apex/reasoning-sessions/reasoning-demo-pr-482/context
curl http://localhost:8000/organizations/org-demo-apex/pull-requests/pr-checkout-api-482/context
```

The context builder assembles pull request, graph neighborhood, evidence, signal, assumption, and sectioned context without invoking GPT.
Milestone 7 adds the reasoning execution engine:

```bash
curl -X POST http://localhost:8000/organizations/org-demo-apex/reasoning-sessions/reasoning-demo-pr-482/run \
  -H 'Content-Type: application/json' \
  -d '{"graph_depth":2}'
curl http://localhost:8000/organizations/org-demo-apex/reasoning-sessions/reasoning-demo-pr-482/result
```

The engine builds canonical context, executes the configured `gpt-5.5` reasoning model when `OPENAI_API_KEY` is present, persists the structured result on the reasoning session, and returns the same result through the read endpoint.
The canonical context-to-report API is available at `POST /reason` for callers that already have a reasoning context payload.
When `OPENAI_API_KEY` is not configured, local development uses a deterministic contract-compatible reasoning path so the application remains runnable.
