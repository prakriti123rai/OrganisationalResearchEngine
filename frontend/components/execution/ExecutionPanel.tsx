import { CheckCircle2, Circle, FilePenLine, Play } from "lucide-react";

import { actionTypeLabel, type SuggestedAction } from "../actions/ActionCard";
import type { ExecutionRecord } from "./ArtifactViewer";

export function ExecutionPanel({
  actions,
  busyActionId,
  executions,
  selectedExecutionId,
  onSelectExecution,
  onStartExecution,
}: {
  actions: SuggestedAction[];
  busyActionId: string | null;
  executions: ExecutionRecord[];
  selectedExecutionId: string | null;
  onSelectExecution: (executionId: string) => void;
  onStartExecution: (action: SuggestedAction) => void;
}) {
  const executedActionIds = new Set(
    executions
      .map((execution) => execution.action_id)
      .filter((actionId): actionId is string => Boolean(actionId)),
  );
  const executableActions = actions.filter(
    (action) =>
      ["approved", "executed"].includes(action.status) &&
      !executedActionIds.has(action.id),
  );
  const completedExecutions = executions.filter(
    (execution) => execution.status === "completed",
  );

  return (
    <section className="min-h-0 overflow-y-auto border border-border bg-background p-5">
      <div className="grid grid-cols-4 gap-3">
        <ExecutionMetric label="Queued" value={executableActions.length} />
        <ExecutionMetric label="Running" value={runningCount(executions)} />
        <ExecutionMetric label="Completed" value={completedExecutions.length} />
        <ExecutionMetric
          label="Artifacts"
          value={
            executions.filter((execution) => Boolean(execution.artifact_type))
              .length
          }
        />
      </div>

      <section className="mt-5 border border-border bg-muted p-5">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold">Pending Automations</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Approved actions enter mock Codex execution and generate
              engineering artifacts without touching production systems.
            </p>
          </div>
        </div>
        <div className="mt-4 grid gap-3">
          {executableActions.length === 0 ? (
            <div className="border border-border bg-background p-4 text-sm text-muted-foreground">
              No approved actions are waiting for artifact generation.
            </div>
          ) : (
            executableActions.map((action) => (
              <article
                className="grid grid-cols-[1fr_auto] gap-4 border border-border bg-background p-4"
                key={action.id}
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-semibold">{action.title}</h3>
                    <span className="border border-border bg-muted px-2 py-1 text-xs text-muted-foreground">
                      {actionTypeLabel(action.action_type)}
                    </span>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-muted-foreground">
                    {action.description}
                  </p>
                </div>
                <button
                  className="inline-flex h-10 items-center justify-center gap-2 border border-confidence/40 bg-confidence/10 px-3 text-sm text-confidence transition hover:bg-confidence/20 disabled:opacity-50"
                  disabled={busyActionId === action.id}
                  onClick={() => onStartExecution(action)}
                  type="button"
                >
                  <Play className="h-4 w-4" />
                  Start
                </button>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="mt-5 border border-border bg-muted p-5">
        <h2 className="text-base font-semibold">Completed Actions</h2>
        <div className="mt-4 grid gap-3">
          {executions.map((execution) => {
            const active = execution.id === selectedExecutionId;
            const StatusIcon =
              execution.status === "completed" ? CheckCircle2 : Circle;
            return (
              <button
                className={[
                  "w-full border p-4 text-left transition",
                  active
                    ? "border-primary bg-primary/10"
                    : "border-border bg-background hover:border-primary",
                ].join(" ")}
                key={execution.id}
                onClick={() => onSelectExecution(execution.id)}
                type="button"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-sm font-semibold">
                        {execution.artifact_title ?? execution.id}
                      </h3>
                      <span className="border border-border bg-muted px-2 py-1 text-xs text-muted-foreground">
                        {execution.artifact_type
                          ? actionTypeLabel(execution.artifact_type)
                          : "Execution"}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                      <FilePenLine className="h-3.5 w-3.5" />
                      {execution.action_id}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-xs capitalize">
                    <StatusIcon className="h-3.5 w-3.5" />
                    {execution.status}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </section>
    </section>
  );
}

function ExecutionMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-border bg-background p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
    </div>
  );
}

function runningCount(executions: ExecutionRecord[]) {
  return executions.filter((execution) =>
    ["queued", "running"].includes(execution.status),
  ).length;
}
