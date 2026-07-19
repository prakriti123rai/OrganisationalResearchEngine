import { AlertTriangle, ChevronRight } from "lucide-react";

export type ImpactEvidence = {
  id: string;
  title: string;
  summary: string;
  source: string;
};

export type ImpactRisk = {
  id: string;
  title: string;
  summary: string;
  impact: string;
  confidence: string;
  evidence: ImpactEvidence[];
};

export type RiskCardProps = {
  risk: ImpactRisk;
  onSelectEvidence: (evidenceId: string) => void;
};

export function RiskCard({ risk, onSelectEvidence }: RiskCardProps) {
  return (
    <article className="interactive-card border border-risk/40 bg-risk/10 p-4">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-risk" />
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-foreground">
              {risk.title}
            </h3>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">
              {risk.summary}
            </p>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-xs uppercase text-risk">{risk.impact}</div>
          <div className="mt-1 text-xs text-confidence">
            {risk.confidence} confidence
          </div>
        </div>
      </div>

      <details className="mt-4 border border-border bg-background px-3 py-2">
        <summary className="cursor-pointer text-xs font-semibold text-muted-foreground">
          Evidence ({risk.evidence.length})
        </summary>
        <div className="mt-3 space-y-2">
          {risk.evidence.map((evidence) => (
            <button
              className="flex w-full items-start gap-2 border border-border bg-muted px-3 py-2 text-left text-xs transition hover:border-primary hover:text-foreground"
              key={evidence.id}
              onClick={() => onSelectEvidence(evidence.id)}
              type="button"
            >
              <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
              <span className="min-w-0">
                <span className="block font-semibold">{evidence.title}</span>
                <span className="mt-1 block leading-5 text-muted-foreground">
                  {evidence.summary}
                </span>
              </span>
            </button>
          ))}
        </div>
      </details>
    </article>
  );
}
