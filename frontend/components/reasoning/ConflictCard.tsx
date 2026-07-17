export type ConflictCardProps = {
  summary: string;
};

export function ConflictCard({ summary }: ConflictCardProps) {
  return (
    <article className="border border-risk/40 bg-risk/10 p-3">
      <div className="text-sm font-semibold text-risk">Conflict Resolution</div>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">{summary}</p>
    </article>
  );
}
