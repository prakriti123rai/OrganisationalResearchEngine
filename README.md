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
Milestone 3 does not add evidence APIs, graph APIs, or reasoning execution logic.
Those remain reserved for later milestones.
