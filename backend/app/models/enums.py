from enum import Enum


class EntityType(str, Enum):
    ORGANIZATION = "organization"
    TEAM = "team"
    PERSON = "person"
    REPOSITORY = "repository"
    SERVICE = "service"
    PULL_REQUEST = "pull_request"
    DOCUMENT = "document"
    RFC = "rfc"
    RUNBOOK = "runbook"
    INCIDENT = "incident"
    FEATURE = "feature"
    DEPLOYMENT = "deployment"
    EXTERNAL_DEPENDENCY = "external_dependency"


class EntityStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class EvidenceType(str, Enum):
    PULL_REQUEST = "pull_request"
    REPOSITORY = "repository"
    ARCHITECTURE_DOCUMENT = "architecture_document"
    RFC = "rfc"
    RUNBOOK = "runbook"
    INCIDENT = "incident"
    SLACK_DISCUSSION = "slack_discussion"
    OWNERSHIP_METADATA = "ownership_metadata"
    DEPLOYMENT_RECORD = "deployment_record"
    CONFIGURATION = "configuration"


class RelationshipType(str, Enum):
    OWNS = "owns"
    MAINTAINS = "maintains"
    CONTRIBUTES_TO = "contributes_to"
    REVIEWS = "reviews"
    DEPENDS_ON = "depends_on"
    USES = "uses"
    DOCUMENTS = "documents"
    IMPLEMENTS = "implements"
    RELATES_TO = "relates_to"
    RESPONDED_TO = "responded_to"
    DEPLOYS = "deploys"
    AFFECTS = "affects"


class RelationshipProvenance(str, Enum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"


class RelationshipStrength(str, Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SignalType(str, Enum):
    EXPERTISE = "expertise"
    OWNERSHIP_CONFIDENCE = "ownership_confidence"
    HIDDEN_DEPENDENCY = "hidden_dependency"
    SERVICE_COUPLING = "service_coupling"
    CROSS_TEAM_COLLABORATION = "cross_team_collaboration"
    REVIEW_PATTERN = "review_pattern"
    DEPLOYMENT_PATTERN = "deployment_pattern"
    OPERATIONAL_HABIT = "operational_habit"
    COMMUNICATION_PATTERN = "communication_pattern"
    KNOWLEDGE_CONCENTRATION = "knowledge_concentration"
    DOCUMENTATION_COVERAGE = "documentation_coverage"
    ORGANIZATIONAL_RISK = "organizational_risk"


class AssumptionType(str, Enum):
    OWNERSHIP = "ownership"
    DEPENDENCY = "dependency"
    OPERATIONAL = "operational"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    COMMUNICATION = "communication"
    EXPERTISE = "expertise"
    RISK = "risk"


class AssumptionStatus(str, Enum):
    ACTIVE = "active"
    CHALLENGED = "challenged"
    INVALIDATED = "invalidated"


class PullRequestStatus(str, Enum):
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"


class ReasoningSessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
