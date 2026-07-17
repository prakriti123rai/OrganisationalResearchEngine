import { Gauge, GitBranch, ShieldCheck, Users } from "lucide-react";
import type { ReactNode } from "react";

import { AffectedServices, type AffectedService } from "./AffectedServices";
import { RiskCard, type ImpactEvidence, type ImpactRisk } from "./RiskCard";

export type ImpactSummaryData = {
  answer: string;
  impactLevel: string;
  confidence: string;
  affectedTeams: string[];
  services: AffectedService[];
  risks: ImpactRisk[];
  riskTimeline: string[];
  selectedEvidence: ImpactEvidence | null;
  primaryEvidence: ImpactEvidence[];
};

export type ImpactSummaryProps = {
  report: ImpactSummaryData;
  onSelectEvidence: (evidenceId: string) => void;
};

export function ImpactSummary({
  report,
  onSelectEvidence,
}: ImpactSummaryProps) {
  return (
    <div className="grid h-[calc(100vh-190px)] grid-cols-[1fr_360px] gap-5">
      <section className="min-h-0 overflow-y-auto border border-border bg-background p-5">
        <div className="grid grid-cols-[1fr_180px_180px] gap-4">
          <div className="border border-border bg-muted p-4">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <GitBranch className="h-4 w-4 text-primary" />
              Impact Summary
            </div>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              {report.answer}
            </p>
          </div>
          <ImpactStat
            icon={<Gauge className="h-4 w-4 text-risk" />}
            label="Risk"
            value={report.impactLevel}
          />
          <ImpactStat
            icon={<ShieldCheck className="h-4 w-4 text-confidence" />}
            label="Confidence"
            value={report.confidence}
          />
        </div>

        <div className="mt-5 grid grid-cols-[0.9fr_1.1fr] gap-5">
          <section className="border border-border bg-muted p-5">
            <div className="flex items-center gap-3">
              <Users className="h-4 w-4 text-primary" />
              <h2 className="text-base font-semibold">Affected Teams</h2>
            </div>
            <div className="mt-4 grid gap-3">
              {report.affectedTeams.map((team) => (
                <div
                  className="border border-border bg-background px-3 py-2 text-sm"
                  key={team}
                >
                  {team}
                </div>
              ))}
            </div>
          </section>

          <section className="border border-border bg-muted p-5">
            <h2 className="text-base font-semibold">Risk Timeline</h2>
            <div className="mt-4 space-y-3">
              {report.riskTimeline.map((item, index) => (
                <div
                  className="grid grid-cols-[28px_1fr] gap-3 text-sm"
                  key={item}
                >
                  <div className="grid h-7 w-7 place-items-center border border-primary/40 bg-primary/10 text-xs text-primary">
                    {index + 1}
                  </div>
                  <div className="border border-border bg-background px-3 py-2 text-muted-foreground">
                    {item}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="mt-5">
          <AffectedServices
            onSelectEvidence={onSelectEvidence}
            services={report.services}
          />
        </div>

        <section className="mt-5 border border-border bg-muted p-5">
          <h2 className="text-base font-semibold">Evidence-Backed Risks</h2>
          <div className="mt-4 grid gap-3">
            {report.risks.map((risk) => (
              <RiskCard
                key={risk.id}
                onSelectEvidence={onSelectEvidence}
                risk={risk}
              />
            ))}
          </div>
        </section>
      </section>

      <aside className="min-h-0 overflow-y-auto border border-border bg-muted p-4">
        <section className="border border-border bg-background p-4">
          <h2 className="text-sm font-semibold">Selected Evidence</h2>
          {report.selectedEvidence ? (
            <article className="mt-3">
              <div className="text-sm font-semibold">
                {report.selectedEvidence.title}
              </div>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">
                {report.selectedEvidence.summary}
              </p>
              <div className="mt-3 text-xs text-muted-foreground">
                {report.selectedEvidence.source}
              </div>
            </article>
          ) : (
            <p className="mt-3 text-xs text-muted-foreground">
              Select evidence from a risk or affected service.
            </p>
          )}
        </section>

        <section className="mt-5 border border-border bg-background p-4">
          <h2 className="text-sm font-semibold">Primary Evidence</h2>
          <div className="mt-3 space-y-2">
            {report.primaryEvidence.map((evidence) => (
              <button
                className="w-full border border-border bg-muted px-3 py-2 text-left text-xs transition hover:border-primary hover:text-foreground"
                key={evidence.id}
                onClick={() => onSelectEvidence(evidence.id)}
                type="button"
              >
                <span className="block font-semibold">{evidence.title}</span>
                <span className="mt-1 block text-muted-foreground">
                  {evidence.source}
                </span>
              </button>
            ))}
          </div>
        </section>
      </aside>
    </div>
  );
}

function ImpactStat({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="border border-border bg-muted p-4">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>
      <div className="mt-3 text-2xl font-semibold capitalize">{value}</div>
    </div>
  );
}
