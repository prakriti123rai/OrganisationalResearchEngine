import { CheckCircle2, Circle, FilePenLine, XCircle } from "lucide-react";

export type SuggestedAction = {
  id: string;
  action_type: string;
  title: string;
  description: string;
  status: string;
  confidence: string;
  payload: Record<string, unknown>;
};

export type ActionCardProps = {
  action: SuggestedAction;
  active: boolean;
  onSelect: (action: SuggestedAction) => void;
};

export function ActionCard({ action, active, onSelect }: ActionCardProps) {
  const StatusIcon = statusIcon(action.status);

  return (
    <button
      className={[
        "interactive-card w-full border p-4 text-left transition",
        active
          ? "border-primary bg-primary/10"
          : "border-border bg-muted hover:border-primary hover:bg-accent/60",
      ].join(" ")}
      onClick={() => onSelect(action)}
      type="button"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold">{action.title}</h3>
            <span className="rounded-md border border-border bg-background px-2 py-1 text-xs text-muted-foreground">
              {actionTypeLabel(action.action_type)}
            </span>
          </div>
          <p className="mt-2 text-xs leading-5 text-muted-foreground">
            {action.description}
          </p>
        </div>
        <div className="shrink-0 text-right">
          <div className="flex items-center justify-end gap-1 text-xs capitalize text-foreground">
            <StatusIcon className="h-3.5 w-3.5" />
            {action.status}
          </div>
          <div className="mt-2 text-xs text-confidence">
            {action.confidence} confidence
          </div>
        </div>
      </div>
    </button>
  );
}

export function actionTypeLabel(value: string) {
  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function statusIcon(status: string) {
  if (status === "approved") {
    return CheckCircle2;
  }
  if (status === "rejected") {
    return XCircle;
  }
  if (status === "executed") {
    return FilePenLine;
  }
  return Circle;
}
