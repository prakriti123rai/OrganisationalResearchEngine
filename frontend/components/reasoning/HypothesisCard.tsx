export type HypothesisCardProps = {
  title: string;
  summary: string;
  confidence?: string | null;
  evidenceIds: string[];
  assumptionIds: string[];
};

export function HypothesisCard({
  title,
  summary,
  confidence,
  evidenceIds,
  assumptionIds,
}: HypothesisCardProps) {
  return (
    <article className="interactive-card border border-primary/35 bg-primary/10 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="text-sm font-semibold">{title}</div>
        {confidence && (
          <span className="rounded-md border border-border bg-background px-2 py-1 text-xs text-muted-foreground">
            {confidence}
          </span>
        )}
      </div>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">{summary}</p>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div className="border border-border bg-background px-2 py-1">
          Evidence {evidenceIds.length}
        </div>
        <div className="border border-border bg-background px-2 py-1">
          Assumptions {assumptionIds.length}
        </div>
      </div>
    </article>
  );
}
