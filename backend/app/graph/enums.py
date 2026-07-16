from enum import Enum


class EntityLabel(str, Enum):
    ORGANIZATION = "Organization"
    TEAM = "Team"
    PERSON = "Person"
    REPOSITORY = "Repository"
    SERVICE = "Service"
    PULL_REQUEST = "PullRequest"
    FEATURE = "Feature"
    DOCUMENT = "Document"
    INCIDENT = "Incident"
    RUNBOOK = "Runbook"
    RFC = "RFC"
    DEPLOYMENT = "Deployment"
    EXTERNAL_DEPENDENCY = "ExternalDependency"


class GraphRelationshipType(str, Enum):
    OWNS = "OWNS"
    MAINTAINS = "MAINTAINS"
    CONTRIBUTES_TO = "CONTRIBUTES_TO"
    REVIEWS = "REVIEWS"
    DEPENDS_ON = "DEPENDS_ON"
    USES = "USES"
    DOCUMENTS = "DOCUMENTS"
    IMPLEMENTS = "IMPLEMENTS"
    RELATES_TO = "RELATES_TO"
    RESPONDED_TO = "RESPONDED_TO"
    DEPLOYS = "DEPLOYS"
    AFFECTS = "AFFECTS"
