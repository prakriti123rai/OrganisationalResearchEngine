# ORE Hackathon Demo

## Goal

Show that ORE understands the organization before a risky pull request merges.
The demo should feel like evidence-backed organizational reasoning, not search or chat.

## Reset

Start Docker Compose and reset the seeded workflow:

```bash
docker compose up -d --build
python3 reset_demo.py
```

The reset script reseeds Apex Demo Organization, syncs Neo4j, runs the reasoning session, generates suggested actions, and preloads one generated Codex artifact.

## Hero Workflow

The canonical hero change is `Route express checkout authorization through risk scoring`.
It appears as `checkout-api` PR #482.
The reasoning session id is `reasoning-demo-pr-482`.

## Screens

1. Dashboard
   Show organization health, knowledge score, recent reasoning, recent predictions, activity, and graph preview.

2. Evidence
   Show the seeded pull request, RFC, runbook, incident, ownership, Slack, deployment, and storefront evidence.

3. Graph
   Show the interactive organizational graph and the evidence-backed relationship list.

4. Reasoning
   Show the animated reasoning timeline.
   Point out evidence collection, graph expansion, signals, assumptions, conflicts, predictions, and planned actions.

5. Impact
   Show affected services, affected teams, high risk, confidence, and selectable evidence.

6. Actions
   Show generated runbook, architecture, reviewer, Slack, checklist, documentation, and PR summary actions.
   Approve one proposed action if you want to demonstrate the approval flow live.

7. Execution
   Show the generated Codex artifact, execution logs, artifact filename, and the no-production-changes safety boundary.

## Success Criteria

- Docker starts.
- PostgreSQL is healthy.
- Neo4j is healthy.
- Backend `/health` is `ok`.
- Frontend returns HTTP 200.
- Dashboard is populated.
- Evidence Explorer has seeded evidence.
- Graph renders nodes and relationships.
- Reasoning timeline animates and exposes evidence.
- Impact report shows confidence and affected services.
- Actions are generated and approvable.
- Execution Center shows generated artifacts and logs.
- No generic `Loading...` messages appear.
- No runtime errors appear in backend or frontend logs.

## Useful Commands

```bash
curl http://localhost:8000/health
curl http://localhost:8000/dashboard?organization_id=org-demo-apex
curl http://localhost:8000/organizations/org-demo-apex/evidence
curl -X POST http://localhost:8000/organizations/org-demo-apex/graph/sync
curl http://localhost:8000/organizations/org-demo-apex/graph/neo4j
curl -X POST http://localhost:8000/organizations/org-demo-apex/reasoning-sessions/reasoning-demo-pr-482/run \
  -H 'Content-Type: application/json' \
  -d '{"graph_depth":2}'
curl -X POST http://localhost:8000/actions/generate \
  -H 'Content-Type: application/json' \
  -d '{"organization_id":"org-demo-apex","reasoning_session_id":"reasoning-demo-pr-482"}'
curl http://localhost:8000/execution/history?organization_id=org-demo-apex
```
