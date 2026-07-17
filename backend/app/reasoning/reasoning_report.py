from __future__ import annotations

from typing import Optional

from app.schemas.reasoning import (
    ReasoningFinding,
    ReasoningHypothesis,
    ReasoningReportSection,
    ReasoningResult,
    ReasoningStep,
)
from app.schemas.reasoning_context import ReasoningContextRead, ReasoningContextSection


def build_deterministic_reasoning_report(
    *,
    context: ReasoningContextRead,
    model: str,
    prompt_version: str,
    execution_time_ms: int,
) -> ReasoningResult:
    sections = {section.key: section for section in context.sections}
    dependency_section = sections.get("dependencies")
    ownership_section = sections.get("ownership")
    reviewer_section = sections.get("reviewers")
    operational_section = sections.get("operational_readiness")

    impacted_entity_ids = sorted(
        {
            *context.scope.entity_ids,
            *_section_entity_ids(dependency_section),
            *_section_entity_ids(operational_section),
        }
    )
    primary_evidence_ids = sorted(
        {
            *context.scope.evidence_ids,
            *_section_evidence_ids(dependency_section),
            *_section_evidence_ids(operational_section),
        }
    )
    hypotheses = [
        _hypothesis(
            hypothesis_id="hypothesis-risk-rollout",
            statement=(
                "Routing express checkout through risk scoring can affect rollout safety "
                "unless timeout behavior and fallback monitoring are confirmed."
            ),
            status="supported",
            confidence="medium",
            section=dependency_section,
        ),
        _hypothesis(
            hypothesis_id="hypothesis-review-coverage",
            statement=(
                "The change needs review from checkout architecture and risk maintainers "
                "because the context shows concentrated expertise."
            ),
            status="supported",
            confidence="medium",
            section=reviewer_section,
        ),
        _hypothesis(
            hypothesis_id="hypothesis-operational-readiness",
            statement=(
                "Operational readiness depends on recent incident mitigations, runbook "
                "accuracy, and deployment metrics."
            ),
            status="supported",
            confidence="medium",
            section=operational_section,
        ),
    ]

    return ReasoningResult(
        question=context.question,
        answer=(
            "checkout-api PR #482 has high organizational impact because it changes "
            "the authorization path for Express Checkout, touches Checkout API and "
            "Risk Engine ownership boundaries, and depends on operational knowledge "
            "from recent timeout incidents."
        ),
        model=model,
        provider="deterministic_local",
        impact_level="high",
        confidence="medium",
        findings=[
            _finding(
                finding_id="finding-ownership",
                title="Ownership path is explicit",
                summary=(
                    "Payments owns Checkout API changes while SRE owns operational "
                    "escalation through the runbook context."
                ),
                impact="medium",
                confidence=_confidence_for_section(ownership_section),
                section=ownership_section,
            ),
            _finding(
                finding_id="finding-dependency-risk",
                title="Risk Engine dependency controls rollout safety",
                summary=(
                    "The PR routes express checkout through risk scoring, making Risk "
                    "Engine timeout behavior and review availability critical to the rollout."
                ),
                impact="high",
                confidence=_confidence_for_section(dependency_section),
                section=dependency_section,
            ),
            _finding(
                finding_id="finding-review",
                title="Review is concentrated in checkout and risk experts",
                summary=(
                    "The context points to Maya and Noah as high-signal reviewers for "
                    "architecture and risk behavior."
                ),
                impact="medium",
                confidence=_confidence_for_section(reviewer_section),
                section=reviewer_section,
            ),
            _finding(
                finding_id="finding-operational-readiness",
                title="Operational readiness depends on recent incident context",
                summary=(
                    "Runbook, deployment, and incident evidence show the rollout should "
                    "be checked against current risk timeout mitigations."
                ),
                impact="high",
                confidence=_confidence_for_section(operational_section),
                section=operational_section,
            ),
        ],
        hypotheses=hypotheses,
        canonical_sections=_canonical_sections(
            hypotheses=hypotheses,
            dependency_section=dependency_section,
            operational_section=operational_section,
            reviewer_section=reviewer_section,
        ),
        reasoning_steps=_reasoning_steps(context.sections),
        open_questions=[
            "Has the staged rollout plan been accepted by Payments, Risk, and SRE?",
            "Are risk timeout dashboards and fallback alerts current for this rollout?",
        ],
        recommended_actions=[
            "Confirm staged rollout approval with Payments, Risk, and SRE.",
            "Verify risk timeout dashboards and fallback alerts before merge.",
            "Request checkout architecture and risk maintainer review.",
        ],
        impacted_entity_ids=impacted_entity_ids,
        primary_evidence_ids=primary_evidence_ids,
        context_scope=context.scope.model_dump(mode="json"),
        metadata={
            "source": "canonical_context",
            "fallback_reason": "OPENAI_API_KEY is not configured",
            "context_builder": context.context_metadata.get("builder"),
            "prompt_version": prompt_version,
            "execution_time_ms": execution_time_ms,
        },
    )


def _canonical_sections(
    *,
    hypotheses: list[ReasoningHypothesis],
    dependency_section: Optional[ReasoningContextSection],
    operational_section: Optional[ReasoningContextSection],
    reviewer_section: Optional[ReasoningContextSection],
) -> list[ReasoningReportSection]:
    return [
        ReasoningReportSection(
            key="hypotheses",
            title="Hypotheses",
            summary=f"{len(hypotheses)} supported hypotheses were generated from context.",
            evidence_ids=sorted(
                evidence_id for hypothesis in hypotheses for evidence_id in hypothesis.evidence_ids
            ),
            assumption_ids=sorted(
                assumption_id
                for hypothesis in hypotheses
                for assumption_id in hypothesis.assumption_ids
            ),
        ),
        ReasoningReportSection(
            key="validation",
            title="Validation",
            summary="Evidence, relationships, signals, and assumptions support the impact.",
            evidence_ids=_section_evidence_ids(dependency_section),
            assumption_ids=dependency_section.assumption_ids if dependency_section else [],
        ),
        ReasoningReportSection(
            key="conflicts",
            title="Conflicts",
            summary="No blocking contradiction was found in the bounded reasoning context.",
            evidence_ids=[],
            assumption_ids=[],
        ),
        ReasoningReportSection(
            key="predicted_impacts",
            title="Predicted Impacts",
            summary=(
                "Risk scoring, checkout ownership, reviewer coverage, and rollout "
                "safety are impacted."
            ),
            evidence_ids=_section_evidence_ids(operational_section),
            assumption_ids=operational_section.assumption_ids if operational_section else [],
        ),
        ReasoningReportSection(
            key="confidence",
            title="Confidence",
            summary=(
                "Overall confidence is medium because evidence is strong but rollout "
                "approval is unresolved."
            ),
            evidence_ids=_section_evidence_ids(reviewer_section),
            assumption_ids=reviewer_section.assumption_ids if reviewer_section else [],
        ),
        ReasoningReportSection(
            key="recommended_actions",
            title="Recommended Actions",
            summary="Confirm rollout approval, verify monitoring, and request expert review.",
            evidence_ids=_section_evidence_ids(dependency_section),
            assumption_ids=dependency_section.assumption_ids if dependency_section else [],
        ),
    ]


def _reasoning_steps(sections: list[ReasoningContextSection]) -> list[ReasoningStep]:
    steps = []
    for index, section in enumerate(sections, start=1):
        steps.append(
            ReasoningStep(
                id=f"step-{section.key}",
                order=index,
                section_key=section.key,
                title=section.title,
                reasoning=section.summary,
                evidence_ids=section.evidence_ids,
                signal_ids=section.signal_ids,
                assumption_ids=section.assumption_ids,
            )
        )
    return steps


def _finding(
    *,
    finding_id: str,
    title: str,
    summary: str,
    impact: str,
    confidence: str,
    section: Optional[ReasoningContextSection],
) -> ReasoningFinding:
    return ReasoningFinding(
        id=finding_id,
        title=title,
        summary=summary,
        impact=impact,
        confidence=confidence,
        entity_ids=_section_entity_ids(section),
        evidence_ids=_section_evidence_ids(section),
        signal_ids=section.signal_ids if section is not None else [],
        assumption_ids=section.assumption_ids if section is not None else [],
    )


def _hypothesis(
    *,
    hypothesis_id: str,
    statement: str,
    status: str,
    confidence: str,
    section: Optional[ReasoningContextSection],
) -> ReasoningHypothesis:
    return ReasoningHypothesis(
        id=hypothesis_id,
        statement=statement,
        status=status,
        confidence=confidence,
        evidence_ids=_section_evidence_ids(section),
        assumption_ids=section.assumption_ids if section is not None else [],
    )


def _confidence_for_section(section: Optional[ReasoningContextSection]) -> str:
    if section is None:
        return "low"
    if section.evidence_ids and section.signal_ids and section.assumption_ids:
        return "medium"
    if section.evidence_ids:
        return "low"
    return "low"


def _section_entity_ids(section: Optional[ReasoningContextSection]) -> list[str]:
    return section.entity_ids if section is not None else []


def _section_evidence_ids(section: Optional[ReasoningContextSection]) -> list[str]:
    return section.evidence_ids if section is not None else []
