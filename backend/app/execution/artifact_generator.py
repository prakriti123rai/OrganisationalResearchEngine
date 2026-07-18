from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.action import Action


@dataclass(frozen=True)
class GeneratedArtifact:
    artifact_type: str
    artifact_title: str
    file_name: str
    content: str
    metadata: dict[str, Any]


class ArtifactGenerator:
    def generate(self, action: Action) -> GeneratedArtifact:
        artifact_type = self._artifact_type(action.action_type)
        artifact_title = self._artifact_title(action)
        file_name = self._file_name(action.action_type)
        evidence_ids = self._evidence_ids(action)
        content = self._content(
            action=action,
            artifact_type=artifact_type,
            artifact_title=artifact_title,
            evidence_ids=evidence_ids,
        )
        return GeneratedArtifact(
            artifact_type=artifact_type,
            artifact_title=artifact_title,
            file_name=file_name,
            content=content,
            metadata={
                "file_name": file_name,
                "evidence_ids": evidence_ids,
                "production_changes": False,
                "generated_by": "codex_adapter",
            },
        )

    def _content(
        self,
        *,
        action: Action,
        artifact_type: str,
        artifact_title: str,
        evidence_ids: list[str],
    ) -> str:
        preview = action.payload.get("artifact_preview")
        preview_text = preview if isinstance(preview, str) else action.description
        evidence_block = "\n".join(f"- {evidence_id}" for evidence_id in evidence_ids)
        return "\n".join(
            [
                f"# {artifact_title}",
                "",
                f"Artifact type: {artifact_type}",
                f"Source action: {action.title}",
                "",
                "## Generated Content",
                preview_text,
                "",
                "## Evidence",
                evidence_block or "- No evidence ids were attached.",
                "",
                "## Safety Boundary",
                "Codex generated this artifact preview only.",
                "No repository, Slack, runbook, or production system was modified.",
            ]
        )

    def _artifact_type(self, action_type: str) -> str:
        return {
            "runbook_update": "runbook_update",
            "architecture_update": "architecture_note",
            "reviewer_assignment": "review_assignment",
            "slack_draft": "slack_announcement",
            "migration_checklist": "migration_checklist",
            "documentation_update": "documentation_update",
            "pr_draft_summary": "pull_request_draft",
        }.get(action_type, "engineering_artifact")

    def _artifact_title(self, action: Action) -> str:
        return f"Codex artifact - {action.title}"

    def _file_name(self, action_type: str) -> str:
        return {
            "runbook_update": "checkout-incident-runbook-update.md",
            "architecture_update": "checkout-risk-routing-architecture-note.md",
            "reviewer_assignment": "checkout-risk-reviewer-assignment.md",
            "slack_draft": "checkout-risk-rollout-announcement.md",
            "migration_checklist": "checkout-risk-migration-checklist.md",
            "documentation_update": "express-checkout-risk-routing-docs.md",
            "pr_draft_summary": "pr-482-approval-summary.md",
        }.get(action_type, f"{action_type.replace('_', '-')}.md")

    def _evidence_ids(self, action: Action) -> list[str]:
        evidence_ids = action.payload.get("evidence_ids")
        if not isinstance(evidence_ids, list):
            return []
        return sorted({item for item in evidence_ids if isinstance(item, str)})
