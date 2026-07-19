import { Check, Pencil, Save, ShieldCheck, X } from "lucide-react";
import { useEffect, useState } from "react";

import { actionTypeLabel, type SuggestedAction } from "./ActionCard";

export type ApprovalPanelProps = {
  action: SuggestedAction | null;
  busyActionId: string | null;
  onApprove: (action: SuggestedAction) => void;
  onReject: (action: SuggestedAction) => void;
  onSave: (
    action: SuggestedAction,
    changes: {
      title: string;
      description: string;
      artifact_preview: string;
    },
  ) => void;
};

export function ApprovalPanel({
  action,
  busyActionId,
  onApprove,
  onReject,
  onSave,
}: ApprovalPanelProps) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [artifactPreview, setArtifactPreview] = useState("");

  useEffect(() => {
    setEditing(false);
    setTitle(action?.title ?? "");
    setDescription(action?.description ?? "");
    setArtifactPreview(artifactPreviewFrom(action));
  }, [action]);

  if (!action) {
    return (
      <aside className="polished-panel grid min-h-[360px] place-items-center border p-5 text-sm text-muted-foreground">
        Select a generated action for approval.
      </aside>
    );
  }

  const disabled = busyActionId === action.id;
  const canEdit = action.status === "proposed";
  const canApprove = action.status === "proposed";
  const canReject = action.status === "proposed";

  return (
    <aside className="polished-panel min-h-0 overflow-y-auto border p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="text-xs text-muted-foreground">
            {actionTypeLabel(action.action_type)}
          </div>
          {editing ? (
            <input
              className="mt-2 h-10 w-full border border-border bg-background px-3 text-sm font-semibold outline-none focus:border-primary"
              onChange={(event) => setTitle(event.target.value)}
              value={title}
            />
          ) : (
            <h2 className="mt-2 text-lg font-semibold">{action.title}</h2>
          )}
        </div>
        <div className="interactive-card border border-confidence/40 bg-confidence/10 px-3 py-2 text-right">
          <div className="flex items-center justify-end gap-1 text-xs text-confidence">
            <ShieldCheck className="h-3.5 w-3.5" />
            {action.confidence}
          </div>
          <div className="mt-1 text-xs capitalize text-muted-foreground">
            {action.status}
          </div>
        </div>
      </div>

      <section className="interactive-card mt-5 border border-border bg-background p-4">
        <h3 className="text-sm font-semibold">Action Plan</h3>
        {editing ? (
          <textarea
            className="mt-3 h-28 w-full resize-none border border-border bg-muted p-3 text-sm leading-6 outline-none focus:border-primary"
            onChange={(event) => setDescription(event.target.value)}
            value={description}
          />
        ) : (
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            {action.description}
          </p>
        )}
      </section>

      <section className="interactive-card mt-5 border border-border bg-background p-4">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold">Artifact Preview</h3>
          <span className="text-xs text-muted-foreground">Codex ready</span>
        </div>
        {editing ? (
          <textarea
            className="mt-3 h-32 w-full resize-none border border-border bg-muted p-3 text-sm leading-6 outline-none focus:border-primary"
            onChange={(event) => setArtifactPreview(event.target.value)}
            value={artifactPreview}
          />
        ) : (
          <p className="mt-3 border border-border bg-muted p-3 text-sm leading-6 text-muted-foreground">
            {artifactPreview}
          </p>
        )}
      </section>

      <section className="interactive-card mt-5 border border-border bg-background p-4">
        <h3 className="text-sm font-semibold">Evidence</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {evidenceIdsFrom(action).map((evidenceId) => (
            <span
              className="border border-border bg-accent px-2 py-1 text-xs text-muted-foreground"
              key={evidenceId}
            >
              {evidenceId}
            </span>
          ))}
        </div>
      </section>

      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
        {editing ? (
          <button
            className="interactive-card inline-flex h-10 items-center justify-center gap-2 rounded-md border border-confidence/40 bg-confidence/10 text-sm text-confidence transition hover:bg-confidence/20 disabled:opacity-50"
            disabled={
              disabled || title.trim() === "" || description.trim() === ""
            }
            onClick={() =>
              onSave(action, {
                title: title.trim(),
                description: description.trim(),
                artifact_preview: artifactPreview.trim(),
              })
            }
            type="button"
          >
            <Save className="h-4 w-4" />
            Save
          </button>
        ) : (
          <button
            className="interactive-card inline-flex h-10 items-center justify-center gap-2 rounded-md border border-border text-sm text-muted-foreground transition hover:border-primary hover:text-foreground disabled:opacity-50"
            disabled={!canEdit || disabled}
            onClick={() => setEditing(true)}
            type="button"
          >
            <Pencil className="h-4 w-4" />
            Edit
          </button>
        )}
        <button
          className="interactive-card inline-flex h-10 items-center justify-center gap-2 rounded-md border border-confidence/40 bg-confidence/10 text-sm text-confidence transition hover:bg-confidence/20 disabled:opacity-50"
          disabled={!canApprove || disabled}
          onClick={() => onApprove(action)}
          type="button"
        >
          <Check className="h-4 w-4" />
          Approve
        </button>
        <button
          className="interactive-card inline-flex h-10 items-center justify-center gap-2 rounded-md border border-risk/40 bg-risk/10 text-sm text-risk transition hover:bg-risk/20 disabled:opacity-50"
          disabled={!canReject || disabled}
          onClick={() => onReject(action)}
          type="button"
        >
          <X className="h-4 w-4" />
          Reject
        </button>
      </div>

      <div className="mt-4 border border-border bg-background px-3 py-2 text-xs text-muted-foreground">
        Approval starts safe Codex artifact generation. Production systems stay
        untouched.
      </div>
    </aside>
  );
}

export function artifactPreviewFrom(action: SuggestedAction | null) {
  const preview = action?.payload.artifact_preview;
  return typeof preview === "string" ? preview : "";
}

function evidenceIdsFrom(action: SuggestedAction) {
  const evidenceIds = action.payload.evidence_ids;
  return Array.isArray(evidenceIds)
    ? evidenceIds.filter((item): item is string => typeof item === "string")
    : [];
}
