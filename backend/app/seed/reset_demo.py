from __future__ import annotations

from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import SessionLocal
from app.execution.execution_service import ExecutionService
from app.models.organization import Organization
from app.seed.demo_organization import DEMO_ORGANIZATION_ID, seed_demo_organization
from app.services.actions import ActionService
from app.services.organizational_graph import OrganizationalGraphService
from app.services.reasoning_engine import ReasoningEngineService

REASONING_SESSION_ID = "reasoning-demo-pr-482"
PRELOADED_ACTION_IDS = [
    "action-reasoning-demo-pr-482-documentation-update",
    "action-reasoning-demo-pr-482-architecture-update",
    "action-reasoning-demo-pr-482-reviewer-assignment",
    "action-reasoning-demo-pr-482-slack-draft",
    "action-reasoning-demo-pr-482-migration-checklist",
]


def reset_demo(session: Session) -> dict[str, Any]:
    session.execute(delete(Organization).where(Organization.id == DEMO_ORGANIZATION_ID))
    session.commit()

    seed_summary = seed_demo_organization(session)
    _clear_neo4j_demo_graph()
    graph_sync = OrganizationalGraphService(session).sync_to_neo4j(
        organization_id=DEMO_ORGANIZATION_ID
    )
    reasoning = ReasoningEngineService(session).run_session(
        organization_id=DEMO_ORGANIZATION_ID,
        reasoning_session_id=REASONING_SESSION_ID,
        graph_depth=2,
        force=True,
    )
    action_plan = ActionService(session).generate_actions(
        organization_id=DEMO_ORGANIZATION_ID,
        reasoning_session_id=REASONING_SESSION_ID,
        force=True,
    )
    action_service = ActionService(session)
    approved_actions = [
        action_service.approve_action(action_id=action_id) for action_id in PRELOADED_ACTION_IDS
    ]
    execution = ExecutionService(session).get_execution(
        execution_id=f"execution-{PRELOADED_ACTION_IDS[0]}",
        organization_id=DEMO_ORGANIZATION_ID,
    )

    return {
        "organization_id": DEMO_ORGANIZATION_ID,
        "seed": seed_summary,
        "graph": {
            "nodes": graph_sync.nodes_synced,
            "edges": graph_sync.edges_synced,
        },
        "reasoning": {
            "session_id": reasoning.reasoning_session.id,
            "status": reasoning.reasoning_session.status,
            "impact_level": reasoning.result.impact_level,
            "confidence": reasoning.result.confidence,
            "findings": len(reasoning.result.findings),
        },
        "actions": {
            "generated": len(action_plan.actions),
            "preloaded_approved_action_ids": [action.id for action in approved_actions],
            "preloaded_approved_statuses": [action.status for action in approved_actions],
        },
        "execution": {
            "id": execution.id,
            "status": execution.status,
            "artifact_type": execution.artifact_type,
            "production_changes": execution.result_metadata.get("production_changes"),
        },
    }


def _clear_neo4j_demo_graph() -> None:
    settings = get_settings()
    try:
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        try:
            with driver.session() as session:
                session.run(
                    "MATCH (n {organization_id: $organization_id}) DETACH DELETE n",
                    organization_id=DEMO_ORGANIZATION_ID,
                )
        finally:
            driver.close()
    except (Neo4jError, ServiceUnavailable, OSError) as exc:
        raise RuntimeError(f"Unable to clear Neo4j demo graph: {exc}") from exc


def main() -> None:
    session = SessionLocal()
    try:
        summary = reset_demo(session)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print(f"Reset {DEMO_ORGANIZATION_ID}")
    print(f"Seed counts: {summary['seed']}")
    print(f"Neo4j graph: {summary['graph']['nodes']} nodes, {summary['graph']['edges']} edges")
    print(
        "Reasoning: "
        f"{summary['reasoning']['status']} "
        f"{summary['reasoning']['impact_level']} "
        f"{summary['reasoning']['confidence']}"
    )
    print(f"Actions generated: {summary['actions']['generated']}")
    print(
        "Preloaded execution: "
        f"{summary['execution']['id']} "
        f"{summary['execution']['status']} "
        f"{summary['execution']['artifact_type']}"
    )


if __name__ == "__main__":
    main()
