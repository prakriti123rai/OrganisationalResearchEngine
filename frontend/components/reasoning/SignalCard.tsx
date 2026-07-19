export type SignalCardProps = {
  title: string;
  summary: string;
  confidence?: string | null;
};

export function SignalCard({ title, summary, confidence }: SignalCardProps) {
  return (
    <article className="interactive-card border border-border bg-background p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="text-sm font-semibold">{title}</div>
        {confidence && (
          <span className="rounded-md border border-confidence/40 bg-confidence/10 px-2 py-1 text-xs text-confidence">
            {confidence}
          </span>
        )}
      </div>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">{summary}</p>
    </article>
  );
}
