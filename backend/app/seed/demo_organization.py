from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypeVar

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.assumption import Assumption
from app.models.entity import Entity
from app.models.evidence import Evidence
from app.models.organization import Organization
from app.models.organizational_signal import OrganizationalSignal
from app.models.pull_request import PullRequest
from app.models.reasoning_session import ReasoningSession
from app.models.relationship import EntityRelationship
from app.models.repository import Repository
from app.models.user import User

DEMO_ORGANIZATION_ID = "org-demo-apex"

ModelT = TypeVar(
    "ModelT",
    Organization,
    Entity,
    Repository,
    User,
    PullRequest,
    Evidence,
    EntityRelationship,
    OrganizationalSignal,
    Assumption,
    ReasoningSession,
)


def _ts(day: int, hour: int = 12, minute: int = 0) -> datetime:
    return datetime(2026, 7, day, hour, minute, tzinfo=timezone.utc)


def _upsert(session: Session, model: type[ModelT], values: dict[str, Any]) -> ModelT:
    record = session.get(model, values["id"])
    if record is None:
        record = model(**values)
        session.add(record)
        return record

    for key, value in values.items():
        if key != "id":
            setattr(record, key, value)
    return record


def _link(collection: list[Any], item: Any) -> None:
    item_id = item.id
    if all(existing.id != item_id for existing in collection):
        collection.append(item)


def _upsert_reasoning_session(session: Session, values: dict[str, Any]) -> ReasoningSession:
    record = session.get(ReasoningSession, values["id"])
    if record is None:
        record = ReasoningSession(**values)
        session.add(record)
        return record

    preserved_status = record.status
    preserved_report = record.report
    preserved_completed_at = record.completed_at
    preserved_context_metadata = record.context_metadata

    for key, value in values.items():
        if key != "id":
            setattr(record, key, value)

    if preserved_status == "completed" and preserved_report is not None:
        record.status = preserved_status
        record.report = preserved_report
        record.completed_at = preserved_completed_at
        record.context_metadata = {
            **values.get("context_metadata", {}),
            **preserved_context_metadata,
        }

    return record


def seed_demo_organization(session: Session) -> dict[str, int]:
    organization = _upsert(
        session,
        Organization,
        {
            "id": DEMO_ORGANIZATION_ID,
            "name": "Apex Demo Organization",
            "description": "Seeded organization for ORE demo reasoning workflows.",
            "status": "active",
            "extra_metadata": {
                "demo": True,
                "scenario": "Checkout reliability and ownership review",
            },
        },
    )

    entities = {
        values["id"]: _upsert(session, Entity, values)
        for values in [
            {
                "id": "entity-org-apex",
                "organization_id": organization.id,
                "entity_type": "organization",
                "display_name": "Apex Demo Organization",
                "description": "The demo organization represented in ORE.",
                "status": "active",
                "extra_metadata": {"demo": True},
            },
            {
                "id": "entity-team-platform",
                "organization_id": organization.id,
                "entity_type": "team",
                "display_name": "Platform Team",
                "description": "Owns shared platform services and identity systems.",
                "status": "active",
                "extra_metadata": {"slack_channel": "#platform"},
            },
            {
                "id": "entity-team-payments",
                "organization_id": organization.id,
                "entity_type": "team",
                "display_name": "Payments Team",
                "description": "Owns checkout, payment routing, and revenue workflows.",
                "status": "active",
                "extra_metadata": {"slack_channel": "#payments"},
            },
            {
                "id": "entity-team-growth",
                "organization_id": organization.id,
                "entity_type": "team",
                "display_name": "Growth Team",
                "description": "Owns customer acquisition and storefront experiments.",
                "status": "active",
                "extra_metadata": {"slack_channel": "#growth"},
            },
            {
                "id": "entity-team-sre",
                "organization_id": organization.id,
                "entity_type": "team",
                "display_name": "SRE Team",
                "description": "Owns operational readiness, alerts, and incident response.",
                "status": "active",
                "extra_metadata": {"slack_channel": "#sre"},
            },
            {
                "id": "entity-person-maya",
                "organization_id": organization.id,
                "entity_type": "person",
                "display_name": "Maya Chen",
                "description": "Staff engineer with checkout and platform review context.",
                "status": "active",
                "extra_metadata": {"email": "maya.chen@example.com"},
            },
            {
                "id": "entity-person-eli",
                "organization_id": organization.id,
                "entity_type": "person",
                "display_name": "Eli Rivera",
                "description": "Payments engineer authoring the checkout migration PR.",
                "status": "active",
                "extra_metadata": {"email": "eli.rivera@example.com"},
            },
            {
                "id": "entity-person-sam",
                "organization_id": organization.id,
                "entity_type": "person",
                "display_name": "Sam Patel",
                "description": "Growth engineer responsible for storefront integration.",
                "status": "active",
                "extra_metadata": {"email": "sam.patel@example.com"},
            },
            {
                "id": "entity-person-zoe",
                "organization_id": organization.id,
                "entity_type": "person",
                "display_name": "Zoe Kim",
                "description": "SRE lead for checkout observability and incident response.",
                "status": "active",
                "extra_metadata": {"email": "zoe.kim@example.com"},
            },
            {
                "id": "entity-person-ina",
                "organization_id": organization.id,
                "entity_type": "person",
                "display_name": "Ina Okafor",
                "description": "Identity service maintainer and reviewer.",
                "status": "active",
                "extra_metadata": {"email": "ina.okafor@example.com"},
            },
            {
                "id": "entity-person-noah",
                "organization_id": organization.id,
                "entity_type": "person",
                "display_name": "Noah Singh",
                "description": "Risk engine maintainer and payment rules reviewer.",
                "status": "active",
                "extra_metadata": {"email": "noah.singh@example.com"},
            },
            {
                "id": "entity-repo-checkout-api",
                "organization_id": organization.id,
                "entity_type": "repository",
                "display_name": "checkout-api",
                "description": "API repository for checkout orchestration.",
                "status": "active",
                "extra_metadata": {"language": "Python"},
            },
            {
                "id": "entity-repo-identity",
                "organization_id": organization.id,
                "entity_type": "repository",
                "display_name": "identity-service",
                "description": "Repository for identity and session services.",
                "status": "active",
                "extra_metadata": {"language": "Go"},
            },
            {
                "id": "entity-repo-webapp",
                "organization_id": organization.id,
                "entity_type": "repository",
                "display_name": "storefront-web",
                "description": "Customer storefront application.",
                "status": "active",
                "extra_metadata": {"language": "TypeScript"},
            },
            {
                "id": "entity-repo-observability",
                "organization_id": organization.id,
                "entity_type": "repository",
                "display_name": "observability-config",
                "description": "Alerting and dashboard configuration repository.",
                "status": "active",
                "extra_metadata": {"language": "YAML"},
            },
            {
                "id": "entity-service-checkout",
                "organization_id": organization.id,
                "entity_type": "service",
                "display_name": "Checkout API",
                "description": "Coordinates checkout state, payment authorization, and receipts.",
                "status": "active",
                "extra_metadata": {"tier": "1", "pager": "payments-primary"},
            },
            {
                "id": "entity-service-risk",
                "organization_id": organization.id,
                "entity_type": "service",
                "display_name": "Risk Engine",
                "description": "Evaluates payment risk before authorization.",
                "status": "active",
                "extra_metadata": {"tier": "1", "pager": "risk-primary"},
            },
            {
                "id": "entity-service-identity",
                "organization_id": organization.id,
                "entity_type": "service",
                "display_name": "Identity Service",
                "description": "Issues customer identity and session tokens.",
                "status": "active",
                "extra_metadata": {"tier": "1", "pager": "platform-primary"},
            },
            {
                "id": "entity-external-stripe",
                "organization_id": organization.id,
                "entity_type": "external_dependency",
                "display_name": "Stripe Gateway",
                "description": "External payment gateway used for card authorization.",
                "status": "active",
                "extra_metadata": {"vendor": "Stripe"},
            },
            {
                "id": "entity-feature-express-checkout",
                "organization_id": organization.id,
                "entity_type": "feature",
                "display_name": "Express Checkout",
                "description": "One-click checkout flow for returning customers.",
                "status": "active",
                "extra_metadata": {"launch_stage": "beta"},
            },
            {
                "id": "entity-rfc-checkout",
                "organization_id": organization.id,
                "entity_type": "rfc",
                "display_name": "RFC-104 Checkout Routing Migration",
                "description": "Architecture proposal for routing checkout through risk scoring.",
                "status": "active",
                "extra_metadata": {"document_url": "https://docs.example.com/rfc-104"},
            },
            {
                "id": "entity-runbook-checkout",
                "organization_id": organization.id,
                "entity_type": "runbook",
                "display_name": "Checkout Incident Runbook",
                "description": "Operational runbook for checkout latency and failure incidents.",
                "status": "active",
                "extra_metadata": {"document_url": "https://docs.example.com/runbooks/checkout"},
            },
            {
                "id": "entity-incident-checkout-latency",
                "organization_id": organization.id,
                "entity_type": "incident",
                "display_name": "Checkout Latency Incident",
                "description": "Recent checkout latency incident linked to risk timeout handling.",
                "status": "active",
                "extra_metadata": {"incident_key": "INC-2026-0712"},
            },
            {
                "id": "entity-deployment-checkout",
                "organization_id": organization.id,
                "entity_type": "deployment",
                "display_name": "Checkout API 2026-07-14 Deployment",
                "description": "Deployment that introduced new risk timeout metrics.",
                "status": "active",
                "extra_metadata": {"environment": "production"},
            },
            {
                "id": "entity-pr-checkout-482",
                "organization_id": organization.id,
                "entity_type": "pull_request",
                "display_name": "checkout-api PR #482",
                "description": "Routes express checkout authorization through risk scoring.",
                "status": "active",
                "extra_metadata": {"number": 482, "repository": "checkout-api"},
            },
        ]
    }

    repositories = {
        values["id"]: _upsert(session, Repository, values)
        for values in [
            {
                "id": "repo-checkout-api",
                "organization_id": organization.id,
                "name": "checkout-api",
                "url": "https://github.com/apex-demo/checkout-api",
                "default_branch": "main",
                "status": "active",
                "extra_metadata": {"entity_id": "entity-repo-checkout-api"},
            },
            {
                "id": "repo-identity-service",
                "organization_id": organization.id,
                "name": "identity-service",
                "url": "https://github.com/apex-demo/identity-service",
                "default_branch": "main",
                "status": "active",
                "extra_metadata": {"entity_id": "entity-repo-identity"},
            },
            {
                "id": "repo-storefront-web",
                "organization_id": organization.id,
                "name": "storefront-web",
                "url": "https://github.com/apex-demo/storefront-web",
                "default_branch": "main",
                "status": "active",
                "extra_metadata": {"entity_id": "entity-repo-webapp"},
            },
            {
                "id": "repo-observability-config",
                "organization_id": organization.id,
                "name": "observability-config",
                "url": "https://github.com/apex-demo/observability-config",
                "default_branch": "main",
                "status": "active",
                "extra_metadata": {"entity_id": "entity-repo-observability"},
            },
        ]
    }

    users = {
        values["id"]: _upsert(session, User, values)
        for values in [
            {
                "id": "user-maya",
                "organization_id": organization.id,
                "team_entity_id": "entity-team-platform",
                "name": "Maya Chen",
                "email": "maya.chen@example.com",
                "role": "Staff Engineer",
                "extra_metadata": {"entity_id": "entity-person-maya"},
            },
            {
                "id": "user-eli",
                "organization_id": organization.id,
                "team_entity_id": "entity-team-payments",
                "name": "Eli Rivera",
                "email": "eli.rivera@example.com",
                "role": "Senior Software Engineer",
                "extra_metadata": {"entity_id": "entity-person-eli"},
            },
            {
                "id": "user-sam",
                "organization_id": organization.id,
                "team_entity_id": "entity-team-growth",
                "name": "Sam Patel",
                "email": "sam.patel@example.com",
                "role": "Frontend Engineer",
                "extra_metadata": {"entity_id": "entity-person-sam"},
            },
            {
                "id": "user-zoe",
                "organization_id": organization.id,
                "team_entity_id": "entity-team-sre",
                "name": "Zoe Kim",
                "email": "zoe.kim@example.com",
                "role": "SRE Lead",
                "extra_metadata": {"entity_id": "entity-person-zoe"},
            },
            {
                "id": "user-ina",
                "organization_id": organization.id,
                "team_entity_id": "entity-team-platform",
                "name": "Ina Okafor",
                "email": "ina.okafor@example.com",
                "role": "Service Owner",
                "extra_metadata": {"entity_id": "entity-person-ina"},
            },
            {
                "id": "user-noah",
                "organization_id": organization.id,
                "team_entity_id": "entity-team-payments",
                "name": "Noah Singh",
                "email": "noah.singh@example.com",
                "role": "Risk Engineer",
                "extra_metadata": {"entity_id": "entity-person-noah"},
            },
        ]
    }

    pull_requests = {
        values["id"]: _upsert(session, PullRequest, values)
        for values in [
            {
                "id": "pr-checkout-api-482",
                "organization_id": organization.id,
                "repository_id": repositories["repo-checkout-api"].id,
                "author_id": users["user-eli"].id,
                "number": 482,
                "title": "Route express checkout authorization through risk scoring",
                "description": (
                    "Introduces risk scoring before card authorization in express checkout."
                ),
                "status": "open",
                "source_branch": "eli/express-checkout-risk-routing",
                "target_branch": "main",
                "extra_metadata": {
                    "entity_id": "entity-pr-checkout-482",
                    "reviewers": ["maya.chen@example.com", "noah.singh@example.com"],
                    "risk": "Touches checkout, risk, and identity request path.",
                },
                "merged_at": None,
            },
            {
                "id": "pr-storefront-web-271",
                "organization_id": organization.id,
                "repository_id": repositories["repo-storefront-web"].id,
                "author_id": users["user-sam"].id,
                "number": 271,
                "title": "Add express checkout experiment flag",
                "description": "Adds storefront flag and analytics events for express checkout.",
                "status": "merged",
                "source_branch": "sam/express-checkout-flag",
                "target_branch": "main",
                "extra_metadata": {"experiment": "express-checkout-beta"},
                "merged_at": _ts(10, 16, 30),
            },
            {
                "id": "pr-identity-service-133",
                "organization_id": organization.id,
                "repository_id": repositories["repo-identity-service"].id,
                "author_id": users["user-ina"].id,
                "number": 133,
                "title": "Expose session trust claims for checkout",
                "description": "Adds trust claims consumed by checkout risk scoring.",
                "status": "open",
                "source_branch": "ina/checkout-trust-claims",
                "target_branch": "main",
                "extra_metadata": {"linked_pull_request_id": "pr-checkout-api-482"},
                "merged_at": None,
            },
        ]
    }

    evidence = {
        values["id"]: _upsert(session, Evidence, values)
        for values in [
            {
                "id": "evidence-pr-checkout-482",
                "organization_id": organization.id,
                "author_id": users["user-eli"].id,
                "evidence_type": "pull_request",
                "source": "github",
                "source_reference": "apex-demo/checkout-api#482",
                "title": "PR #482 routes express checkout through risk scoring",
                "summary": (
                    "The pull request moves express checkout authorization behind "
                    "risk scoring and adds timeout handling for gateway fallbacks."
                ),
                "timestamp": _ts(15, 9, 10),
                "extra_metadata": {"pull_request_id": pull_requests["pr-checkout-api-482"].id},
            },
            {
                "id": "evidence-rfc-checkout-routing",
                "organization_id": organization.id,
                "author_id": users["user-maya"].id,
                "evidence_type": "rfc",
                "source": "docs",
                "source_reference": "RFC-104",
                "title": "RFC-104 checkout routing migration",
                "summary": (
                    "The RFC states that checkout should call risk scoring before "
                    "authorization and keep a fallback path for gateway timeouts."
                ),
                "timestamp": _ts(4, 11, 0),
                "extra_metadata": {"entity_id": "entity-rfc-checkout"},
            },
            {
                "id": "evidence-runbook-checkout",
                "organization_id": organization.id,
                "author_id": users["user-zoe"].id,
                "evidence_type": "runbook",
                "source": "docs",
                "source_reference": "runbooks/checkout",
                "title": "Checkout incident runbook",
                "summary": (
                    "The runbook documents checkout latency alerts, risk timeout "
                    "mitigation, and escalation to Payments and SRE."
                ),
                "timestamp": _ts(8, 13, 0),
                "extra_metadata": {"entity_id": "entity-runbook-checkout"},
            },
            {
                "id": "evidence-incident-checkout-latency",
                "organization_id": organization.id,
                "author_id": users["user-zoe"].id,
                "evidence_type": "incident",
                "source": "incident_management",
                "source_reference": "INC-2026-0712",
                "title": "Checkout latency incident",
                "summary": (
                    "A checkout latency incident was caused by slow risk responses "
                    "and required a temporary fallback rule owned by Payments."
                ),
                "timestamp": _ts(12, 18, 45),
                "extra_metadata": {"severity": "sev2"},
            },
            {
                "id": "evidence-ownership-checkout",
                "organization_id": organization.id,
                "author_id": users["user-maya"].id,
                "evidence_type": "ownership_metadata",
                "source": "catalog",
                "source_reference": "services/checkout-api",
                "title": "Checkout API ownership metadata",
                "summary": (
                    "The service catalog lists Payments as checkout owner and SRE "
                    "as the operational escalation team."
                ),
                "timestamp": _ts(14, 10, 15),
                "extra_metadata": {"tier": "1", "pager": "payments-primary"},
            },
            {
                "id": "evidence-slack-risk-review",
                "organization_id": organization.id,
                "author_id": users["user-noah"].id,
                "evidence_type": "slack_discussion",
                "source": "slack",
                "source_reference": "#payments/2026-07-15-risk-review",
                "title": "Risk review discussion for checkout migration",
                "summary": (
                    "Risk maintainers requested explicit timeout budgets and a "
                    "staged rollout before enabling the checkout routing change."
                ),
                "timestamp": _ts(15, 14, 20),
                "extra_metadata": {"channel": "#payments"},
            },
            {
                "id": "evidence-deployment-checkout",
                "organization_id": organization.id,
                "author_id": users["user-zoe"].id,
                "evidence_type": "deployment_record",
                "source": "deployments",
                "source_reference": "checkout-api/prod/2026-07-14",
                "title": "Checkout API production deployment",
                "summary": (
                    "The latest checkout deployment added risk timeout metrics "
                    "and dashboards used by SRE during rollout."
                ),
                "timestamp": _ts(14, 17, 35),
                "extra_metadata": {"environment": "production"},
            },
            {
                "id": "evidence-pr-storefront-271",
                "organization_id": organization.id,
                "author_id": users["user-sam"].id,
                "evidence_type": "pull_request",
                "source": "github",
                "source_reference": "apex-demo/storefront-web#271",
                "title": "Storefront express checkout feature flag",
                "summary": (
                    "The merged storefront PR introduced an experiment flag that "
                    "depends on the checkout API express checkout route."
                ),
                "timestamp": _ts(10, 15, 30),
                "extra_metadata": {"pull_request_id": pull_requests["pr-storefront-web-271"].id},
            },
        ]
    }

    relationships = {
        values["id"]: _upsert(session, EntityRelationship, values)
        for values in [
            {
                "id": "rel-payments-owns-checkout",
                "organization_id": organization.id,
                "source_entity_id": "entity-team-payments",
                "target_entity_id": "entity-service-checkout",
                "relationship_type": "owns",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {},
            },
            {
                "id": "rel-platform-owns-identity",
                "organization_id": organization.id,
                "source_entity_id": "entity-team-platform",
                "target_entity_id": "entity-service-identity",
                "relationship_type": "owns",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {},
            },
            {
                "id": "rel-sre-maintains-checkout-runbook",
                "organization_id": organization.id,
                "source_entity_id": "entity-team-sre",
                "target_entity_id": "entity-runbook-checkout",
                "relationship_type": "maintains",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {},
            },
            {
                "id": "rel-checkout-depends-risk",
                "organization_id": organization.id,
                "source_entity_id": "entity-service-checkout",
                "target_entity_id": "entity-service-risk",
                "relationship_type": "depends_on",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {"reason": "authorization risk scoring"},
            },
            {
                "id": "rel-checkout-depends-identity",
                "organization_id": organization.id,
                "source_entity_id": "entity-service-checkout",
                "target_entity_id": "entity-service-identity",
                "relationship_type": "depends_on",
                "provenance": "explicit",
                "strength": "moderate",
                "active": True,
                "extra_metadata": {"reason": "session trust claims"},
            },
            {
                "id": "rel-checkout-uses-stripe",
                "organization_id": organization.id,
                "source_entity_id": "entity-service-checkout",
                "target_entity_id": "entity-external-stripe",
                "relationship_type": "uses",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {"reason": "card authorization"},
            },
            {
                "id": "rel-webapp-depends-checkout",
                "organization_id": organization.id,
                "source_entity_id": "entity-repo-webapp",
                "target_entity_id": "entity-service-checkout",
                "relationship_type": "depends_on",
                "provenance": "inferred",
                "strength": "moderate",
                "active": True,
                "extra_metadata": {"reason": "express checkout experiment flag"},
            },
            {
                "id": "rel-rfc-documents-feature",
                "organization_id": organization.id,
                "source_entity_id": "entity-rfc-checkout",
                "target_entity_id": "entity-feature-express-checkout",
                "relationship_type": "documents",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {},
            },
            {
                "id": "rel-pr-affects-checkout",
                "organization_id": organization.id,
                "source_entity_id": "entity-pr-checkout-482",
                "target_entity_id": "entity-service-checkout",
                "relationship_type": "affects",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {},
            },
            {
                "id": "rel-pr-affects-risk",
                "organization_id": organization.id,
                "source_entity_id": "entity-pr-checkout-482",
                "target_entity_id": "entity-service-risk",
                "relationship_type": "affects",
                "provenance": "inferred",
                "strength": "moderate",
                "active": True,
                "extra_metadata": {},
            },
            {
                "id": "rel-eli-contributes-checkout",
                "organization_id": organization.id,
                "source_entity_id": "entity-person-eli",
                "target_entity_id": "entity-repo-checkout-api",
                "relationship_type": "contributes_to",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {},
            },
            {
                "id": "rel-maya-reviews-checkout",
                "organization_id": organization.id,
                "source_entity_id": "entity-person-maya",
                "target_entity_id": "entity-repo-checkout-api",
                "relationship_type": "reviews",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {},
            },
            {
                "id": "rel-noah-reviews-risk",
                "organization_id": organization.id,
                "source_entity_id": "entity-person-noah",
                "target_entity_id": "entity-service-risk",
                "relationship_type": "reviews",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {},
            },
            {
                "id": "rel-sre-responded-checkout-incident",
                "organization_id": organization.id,
                "source_entity_id": "entity-team-sre",
                "target_entity_id": "entity-incident-checkout-latency",
                "relationship_type": "responded_to",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {},
            },
            {
                "id": "rel-deployment-deploys-checkout",
                "organization_id": organization.id,
                "source_entity_id": "entity-deployment-checkout",
                "target_entity_id": "entity-service-checkout",
                "relationship_type": "deploys",
                "provenance": "explicit",
                "strength": "strong",
                "active": True,
                "extra_metadata": {},
            },
        ]
    }

    signals = {
        values["id"]: _upsert(session, OrganizationalSignal, values)
        for values in [
            {
                "id": "signal-checkout-ownership",
                "organization_id": organization.id,
                "subject_entity_id": "entity-service-checkout",
                "signal_type": "ownership_confidence",
                "summary": (
                    "Checkout ownership is explicit: Payments owns the service and "
                    "SRE maintains the operational runbook."
                ),
                "confidence": "high",
                "extra_metadata": {"owner_team_entity_id": "entity-team-payments"},
            },
            {
                "id": "signal-risk-hidden-dependency",
                "organization_id": organization.id,
                "subject_entity_id": "entity-service-risk",
                "signal_type": "hidden_dependency",
                "summary": (
                    "Checkout changes depend on risk behavior, timeout budgets, "
                    "and reviewer availability from the Risk Engine maintainers."
                ),
                "confidence": "medium",
                "extra_metadata": {"dependent_entity_id": "entity-service-checkout"},
            },
            {
                "id": "signal-maya-checkout-expertise",
                "organization_id": organization.id,
                "subject_entity_id": "entity-person-maya",
                "signal_type": "expertise",
                "summary": (
                    "Maya repeatedly reviews checkout and platform changes and "
                    "authored the current routing RFC."
                ),
                "confidence": "high",
                "extra_metadata": {"domain": "checkout architecture"},
            },
            {
                "id": "signal-checkout-review-concentration",
                "organization_id": organization.id,
                "subject_entity_id": "entity-service-checkout",
                "signal_type": "review_pattern",
                "summary": (
                    "High-impact checkout changes concentrate review through Maya " "and Noah."
                ),
                "confidence": "medium",
                "extra_metadata": {"reviewers": ["entity-person-maya", "entity-person-noah"]},
            },
            {
                "id": "signal-checkout-documentation",
                "organization_id": organization.id,
                "subject_entity_id": "entity-service-checkout",
                "signal_type": "documentation_coverage",
                "summary": (
                    "Checkout has an RFC and operational runbook, but rollout "
                    "steps depend on the recent risk timeout discussion."
                ),
                "confidence": "medium",
                "extra_metadata": {"documents": ["entity-rfc-checkout", "entity-runbook-checkout"]},
            },
        ]
    }

    assumptions = {
        values["id"]: _upsert(session, Assumption, values)
        for values in [
            {
                "id": "assumption-checkout-owner",
                "organization_id": organization.id,
                "subject_entity_id": "entity-service-checkout",
                "assumption_type": "ownership",
                "statement": "Payments is accountable for checkout API changes.",
                "status": "active",
                "confidence": "high",
                "extra_metadata": {"owner_team_entity_id": "entity-team-payments"},
            },
            {
                "id": "assumption-risk-dependency",
                "organization_id": organization.id,
                "subject_entity_id": "entity-service-checkout",
                "assumption_type": "dependency",
                "statement": (
                    "Checkout rollout safety depends on Risk Engine timeout behavior "
                    "and review from Risk maintainers."
                ),
                "status": "active",
                "confidence": "medium",
                "extra_metadata": {"dependency_entity_id": "entity-service-risk"},
            },
            {
                "id": "assumption-maya-reviewer",
                "organization_id": organization.id,
                "subject_entity_id": "entity-person-maya",
                "assumption_type": "review",
                "statement": "Maya should review checkout architecture-impacting changes.",
                "status": "active",
                "confidence": "high",
                "extra_metadata": {"domain": "checkout architecture"},
            },
            {
                "id": "assumption-runbook-current",
                "organization_id": organization.id,
                "subject_entity_id": "entity-runbook-checkout",
                "assumption_type": "operational",
                "statement": "The checkout runbook reflects the current incident response path.",
                "status": "active",
                "confidence": "medium",
                "extra_metadata": {"last_reviewed": "2026-07-08"},
            },
        ]
    }

    _upsert_reasoning_session(
        session,
        {
            "id": "reasoning-demo-pr-482",
            "organization_id": organization.id,
            "pull_request_id": pull_requests["pr-checkout-api-482"].id,
            "question": "What organizational impact could checkout-api PR #482 have?",
            "pattern": "pull_request_impact",
            "status": "pending",
            "context_metadata": {
                "demo": True,
                "focus_pull_request_id": "pr-checkout-api-482",
                "expected_context": [
                    "ownership",
                    "dependencies",
                    "reviewers",
                    "operational readiness",
                ],
            },
            "report": None,
            "completed_at": None,
        },
    )

    session.flush()

    entity_evidence_links = {
        "entity-pr-checkout-482": ["evidence-pr-checkout-482"],
        "entity-service-checkout": [
            "evidence-pr-checkout-482",
            "evidence-rfc-checkout-routing",
            "evidence-runbook-checkout",
            "evidence-ownership-checkout",
            "evidence-deployment-checkout",
        ],
        "entity-service-risk": [
            "evidence-pr-checkout-482",
            "evidence-incident-checkout-latency",
            "evidence-slack-risk-review",
        ],
        "entity-service-identity": ["evidence-pr-checkout-482"],
        "entity-feature-express-checkout": [
            "evidence-rfc-checkout-routing",
            "evidence-pr-storefront-271",
        ],
        "entity-runbook-checkout": ["evidence-runbook-checkout"],
        "entity-incident-checkout-latency": ["evidence-incident-checkout-latency"],
        "entity-deployment-checkout": ["evidence-deployment-checkout"],
        "entity-person-maya": ["evidence-rfc-checkout-routing"],
        "entity-person-noah": ["evidence-slack-risk-review"],
    }

    for entity_id, evidence_ids in entity_evidence_links.items():
        for evidence_id in evidence_ids:
            _link(entities[entity_id].supporting_evidence, evidence[evidence_id])

    relationship_evidence_links = {
        "rel-payments-owns-checkout": ["evidence-ownership-checkout"],
        "rel-checkout-depends-risk": [
            "evidence-rfc-checkout-routing",
            "evidence-incident-checkout-latency",
            "evidence-slack-risk-review",
        ],
        "rel-checkout-depends-identity": ["evidence-pr-checkout-482"],
        "rel-checkout-uses-stripe": ["evidence-rfc-checkout-routing"],
        "rel-webapp-depends-checkout": ["evidence-pr-storefront-271"],
        "rel-rfc-documents-feature": ["evidence-rfc-checkout-routing"],
        "rel-pr-affects-checkout": ["evidence-pr-checkout-482"],
        "rel-pr-affects-risk": ["evidence-pr-checkout-482", "evidence-slack-risk-review"],
        "rel-maya-reviews-checkout": ["evidence-pr-checkout-482", "evidence-rfc-checkout-routing"],
        "rel-noah-reviews-risk": ["evidence-slack-risk-review"],
        "rel-sre-responded-checkout-incident": ["evidence-incident-checkout-latency"],
        "rel-deployment-deploys-checkout": ["evidence-deployment-checkout"],
    }

    for relationship_id, evidence_ids in relationship_evidence_links.items():
        for evidence_id in evidence_ids:
            _link(relationships[relationship_id].supporting_evidence, evidence[evidence_id])

    signal_links = {
        "signal-checkout-ownership": {
            "relationships": ["rel-payments-owns-checkout", "rel-sre-maintains-checkout-runbook"],
            "evidence": ["evidence-ownership-checkout", "evidence-runbook-checkout"],
        },
        "signal-risk-hidden-dependency": {
            "relationships": ["rel-checkout-depends-risk", "rel-pr-affects-risk"],
            "evidence": [
                "evidence-rfc-checkout-routing",
                "evidence-incident-checkout-latency",
                "evidence-slack-risk-review",
            ],
        },
        "signal-maya-checkout-expertise": {
            "relationships": ["rel-maya-reviews-checkout"],
            "evidence": ["evidence-rfc-checkout-routing", "evidence-pr-checkout-482"],
        },
        "signal-checkout-review-concentration": {
            "relationships": ["rel-maya-reviews-checkout", "rel-noah-reviews-risk"],
            "evidence": ["evidence-pr-checkout-482", "evidence-slack-risk-review"],
        },
        "signal-checkout-documentation": {
            "relationships": ["rel-rfc-documents-feature", "rel-sre-maintains-checkout-runbook"],
            "evidence": ["evidence-rfc-checkout-routing", "evidence-runbook-checkout"],
        },
    }

    for signal_id, links in signal_links.items():
        for relationship_id in links["relationships"]:
            _link(signals[signal_id].supporting_relationships, relationships[relationship_id])
        for evidence_id in links["evidence"]:
            _link(signals[signal_id].supporting_evidence, evidence[evidence_id])

    assumption_links = {
        "assumption-checkout-owner": {
            "signals": ["signal-checkout-ownership"],
            "evidence": ["evidence-ownership-checkout"],
        },
        "assumption-risk-dependency": {
            "signals": ["signal-risk-hidden-dependency", "signal-checkout-review-concentration"],
            "evidence": ["evidence-rfc-checkout-routing", "evidence-slack-risk-review"],
        },
        "assumption-maya-reviewer": {
            "signals": ["signal-maya-checkout-expertise", "signal-checkout-review-concentration"],
            "evidence": ["evidence-rfc-checkout-routing", "evidence-pr-checkout-482"],
        },
        "assumption-runbook-current": {
            "signals": ["signal-checkout-documentation"],
            "evidence": ["evidence-runbook-checkout", "evidence-incident-checkout-latency"],
        },
    }

    for assumption_id, links in assumption_links.items():
        for signal_id in links["signals"]:
            _link(assumptions[assumption_id].supporting_signals, signals[signal_id])
        for evidence_id in links["evidence"]:
            _link(assumptions[assumption_id].supporting_evidence, evidence[evidence_id])

    session.commit()

    return {
        "organizations": 1,
        "entities": len(entities),
        "repositories": len(repositories),
        "users": len(users),
        "pull_requests": len(pull_requests),
        "evidence": len(evidence),
        "relationships": len(relationships),
        "signals": len(signals),
        "assumptions": len(assumptions),
        "reasoning_sessions": 1,
    }


def main() -> None:
    session = SessionLocal()
    try:
        summary = seed_demo_organization(session)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    counts = ", ".join(f"{key}={value}" for key, value in summary.items())
    print(f"Seeded {DEMO_ORGANIZATION_ID}: {counts}")


if __name__ == "__main__":
    main()
