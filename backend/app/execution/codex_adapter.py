from __future__ import annotations

from dataclasses import dataclass

from app.execution.artifact_generator import ArtifactGenerator, GeneratedArtifact
from app.models.action import Action


@dataclass(frozen=True)
class CodexExecutionResult:
    artifact: GeneratedArtifact
    logs: list[str]


class CodexAdapter:
    def __init__(self, artifact_generator: ArtifactGenerator | None = None) -> None:
        self.artifact_generator = artifact_generator or ArtifactGenerator()

    def execute(self, action: Action) -> CodexExecutionResult:
        artifact = self.artifact_generator.generate(action)
        return CodexExecutionResult(
            artifact=artifact,
            logs=[
                f"Approval verified for action {action.id}.",
                "Codex artifact generation started in mock execution mode.",
                f"Generated {artifact.artifact_type}: {artifact.file_name}.",
                "Execution completed without production changes.",
            ],
        )
