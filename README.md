# Organizational Reasoning Engine

ORE is the Organizational Reasoning Engine implementation defined by the frozen design documents.
The current MVP is frozen for hackathon demo validation.
It demonstrates the pre-merge organizational reasoning workflow for `checkout-api` PR #482.

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

## Release Demo Reset

Reset and preload the full demo from the repository root:

```bash
python3 reset_demo.py
```

The reset command runs inside the Docker backend by default.
It clears the seeded organization, reseeds canonical demo data, syncs Neo4j, runs the reasoning engine, generates suggested actions, and preloads one approved Codex artifact for the Execution Center.

For local backend development without Docker Compose, run:

```bash
python3 reset_demo.py --local
```

Local mode uses a compatible local Python environment only when the backend dependencies are available.
If they are not available, the command falls back to Docker Compose.
Use local mode only when PostgreSQL and Neo4j are reachable from the host using the values in `.env.example` or `.env`.

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
Milestone 10 adds the action planning workflow:

```bash
curl -X POST http://localhost:8000/actions/generate \
  -H 'Content-Type: application/json' \
  -d '{"organization_id":"org-demo-apex","reasoning_session_id":"reasoning-demo-pr-482"}'
curl -X POST http://localhost:8000/actions/action-reasoning-demo-pr-482-runbook-update/approve
curl -X POST http://localhost:8000/actions/action-reasoning-demo-pr-482-runbook-update/reject
```

Actions are generated from the persisted reasoning result, stored in PostgreSQL, and require explicit approval before any later execution workflow can use them.
Milestone 11 adds the execution center workflow:

```bash
curl -X POST http://localhost:8000/execution/start \
  -H 'Content-Type: application/json' \
  -d '{"organization_id":"org-demo-apex","action_id":"action-reasoning-demo-pr-482-documentation-update"}'
curl http://localhost:8000/execution/history?organization_id=org-demo-apex
curl http://localhost:8000/execution/execution-action-reasoning-demo-pr-482-documentation-update
```

Approval starts safe Codex artifact generation for approved actions, persists execution history, and records logs and artifact metadata without modifying production systems.
Milestone 12 adds the dashboard summary APIs:

```bash
curl http://localhost:8000/dashboard?organization_id=org-demo-apex
curl http://localhost:8000/organization?organization_id=org-demo-apex
```

The dashboard combines organization health, knowledge score, recent PRs, recent reasoning, predictions, recent activity, pending execution, and a Neo4j-backed graph preview.

## Demo Flow

1. Open `http://localhost:3000`.
2. Confirm Dashboard shows Apex Demo Organization, recent reasoning, recent predictions, and the graph preview.
3. Open Evidence to inspect the eight seeded evidence records.
4. Open Graph to inspect the interactive Neo4j-backed organizational graph.
5. Open Reasoning to watch the evidence-backed reasoning timeline.
6. Open Impact to review affected services, risk timeline, confidence, and evidence.
7. Open Actions to review generated actions and the approval controls.
8. Open Execution to inspect the generated Codex artifact and logs.

The canonical hero change is `Route express checkout authorization through risk scoring`.
It is represented by `reasoning-demo-pr-482`, `pr-checkout-api-482`, and `entity-pr-checkout-482`.

## Release Smoke Checks

Run backend checks:

```bash
cd backend
python3 -m compileall app
../backend/.venv/bin/ruff check app migrations
../backend/.venv/bin/black --check app migrations
```

Run frontend checks:

```bash
cd frontend
npm run format
npm run lint
npm run build
```

Run Docker checks:

```bash
docker compose up -d --build
docker compose ps
curl http://localhost:8000/health
curl -I http://localhost:3000
```
