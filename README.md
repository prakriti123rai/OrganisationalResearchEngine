# Organizational Reasoning Engine

ORE is the Organizational Reasoning Engine implementation defined by the frozen design documents.
Milestone 1 provides only the project foundation.

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

## Milestone 1 Scope

This milestone intentionally includes no data model, seed data, evidence APIs, graph APIs, or reasoning logic.
Those are reserved for later milestones.
