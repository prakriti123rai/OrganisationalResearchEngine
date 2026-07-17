export type PredictionCardProps = {
  title: string;
  summary: string;
  confidence?: string | null;
  evidenceCount: number;
};

export function PredictionCard({
  title,
  summary,
  confidence,
  evidenceCount,
}: PredictionCardProps) {
  return (
    <article className="border border-border bg-background p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="text-sm font-semibold">{title}</div>
        {confidence && (
          <span className="rounded-md border border-confidence/40 bg-confidence/10 px-2 py-1 text-xs text-confidence">
            {confidence}
          </span>
        )}
      </div>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">{summary}</p>
      <div className="mt-3 text-xs text-muted-foreground">
        Evidence references: {evidenceCount}
      </div>
    </article>
  );
}
