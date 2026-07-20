import { FileText, ShieldCheck } from "lucide-react";

import { actionTypeLabel } from "../actions/ActionCard";

export type ExecutionRecord = {
  id: string;
  organization_id: string;
  action_id: string | null;
  status: string;
  artifact_type: string | null;
  artifact_title: string | null;
  logs: string | null;
  result_metadata: Record<string, unknown>;
  started_at: string;
  completed_at: string | null;
};

export function ArtifactViewer({
  execution,
}: {
  execution: ExecutionRecord | null;
}) {
  if (!execution) {
    return (
      <aside className="polished-panel grid min-h-[360px] place-items-center border p-5 text-sm text-muted-foreground">
        Select a completed execution to inspect the generated artifact.
      </aside>
    );
  }

  const artifactContent = stringMetadata(
    execution.result_metadata.artifact_content,
  );
  const fileName = stringMetadata(execution.result_metadata.file_name);

  return (
    <aside className="polished-panel min-h-0 overflow-y-auto border p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <FileText className="h-3.5 w-3.5" />
            {execution.artifact_type
              ? actionTypeLabel(execution.artifact_type)
              : "Engineering Artifact"}
          </div>
          <h2 className="mt-2 text-lg font-semibold">
            {execution.artifact_title ?? execution.id}
          </h2>
          {fileName && (
            <div className="mt-2 text-xs text-muted-foreground">{fileName}</div>
          )}
        </div>
        <div className="interactive-card border border-confidence/40 bg-confidence/10 px-3 py-2 text-right">
          <div className="flex items-center justify-end gap-1 text-xs text-confidence">
            <ShieldCheck className="h-3.5 w-3.5" />
            Safe
          </div>
          <div className="mt-1 text-xs capitalize text-muted-foreground">
            {execution.status}
          </div>
        </div>
      </div>

      <section className="interactive-card mt-5 border border-border bg-background p-4">
        <h3 className="text-sm font-semibold">Artifact Preview</h3>
        <pre className="mt-3 whitespace-pre-wrap border border-border bg-muted p-3 text-xs leading-5 text-muted-foreground">
          {artifactContent}
        </pre>
      </section>

      <section className="interactive-card mt-5 border border-border bg-background p-4">
        <h3 className="text-sm font-semibold">Execution Logs</h3>
        <pre className="mt-3 whitespace-pre-wrap border border-border bg-muted p-3 text-xs leading-5 text-muted-foreground">
          {execution.logs ?? "No execution logs recorded."}
        </pre>
      </section>
    </aside>
  );
}

function stringMetadata(value: unknown) {
  return typeof value === "string" ? value : "";
}
