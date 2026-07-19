import { CheckCircle2, Circle, FileCode2, ShieldCheck } from "lucide-react";

import type { ExecutionRecord } from "./ArtifactViewer";

export function ExecutionTimeline({
  execution,
}: {
  execution: ExecutionRecord | null;
}) {
  const steps = [
    {
      label: "Approval Verified",
      complete: Boolean(execution),
    },
    {
      label: "Codex Artifact Generated",
      complete: Boolean(execution?.artifact_type),
    },
    {
      label: "Execution Logs Stored",
      complete: Boolean(execution?.logs),
    },
    {
      label: "Production Systems Untouched",
      complete: execution?.result_metadata.production_changes === false,
    },
  ];

  return (
    <section className="polished-panel border p-4">
      <div className="flex items-center gap-2">
        <FileCode2 className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold">Execution Timeline</h2>
      </div>
      <div className="mt-4 grid gap-3">
        {steps.map((step) => {
          const StepIcon = step.complete ? CheckCircle2 : Circle;
          return (
            <div
              className="interactive-card flex items-center justify-between border border-border bg-background px-3 py-2 text-sm"
              key={step.label}
            >
              <div className="flex items-center gap-2">
                <StepIcon
                  className={[
                    "h-4 w-4",
                    step.complete ? "text-confidence" : "text-muted-foreground",
                  ].join(" ")}
                />
                {step.label}
              </div>
              {step.label.includes("Production") && (
                <ShieldCheck className="h-4 w-4 text-confidence" />
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
