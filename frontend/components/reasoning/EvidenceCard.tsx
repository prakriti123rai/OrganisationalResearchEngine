export type EvidenceCardProps = {
  title: string;
  summary: string;
  evidenceIds: string[];
  onSelectEvidence?: (evidenceId: string) => void;
};

export function EvidenceCard({
  title,
  summary,
  evidenceIds,
  onSelectEvidence,
}: EvidenceCardProps) {
  return (
    <article className="border border-border bg-background p-3">
      <div className="text-sm font-semibold">{title}</div>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">{summary}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {evidenceIds.map((evidenceId) => (
          <button
            className="h-6 rounded-md border border-border bg-accent px-2 text-xs text-muted-foreground transition hover:border-primary hover:text-foreground"
            key={evidenceId}
            onClick={() => onSelectEvidence?.(evidenceId)}
            type="button"
          >
            {evidenceId}
          </button>
        ))}
      </div>
    </article>
  );
}
