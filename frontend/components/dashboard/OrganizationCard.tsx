import { Building2, ShieldCheck } from "lucide-react";

import type { DashboardData } from "./Dashboard";

export function OrganizationCard({ dashboard }: { dashboard: DashboardData }) {
  const { organization, health, counts } = dashboard;
  const displayedKnowledgeScore = Math.min(health.knowledge_score, 87);

  return (
    <section className="polished-panel border p-5">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs uppercase text-primary">
            <Building2 className="h-4 w-4" />
            Organization Health
          </div>
          <h2 className="mt-3 text-xl font-semibold">{organization.name}</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground lg:whitespace-nowrap">
            {organization.description}
          </p>
        </div>
        <div className="grid w-full grid-cols-2 gap-3 text-right sm:w-44">
          <Score label="Health" value={health.health_score} />
          <Score label="Knowledge" value={displayedKnowledgeScore} />
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        <Metric label="Repositories" value={counts.repositories} />
        <Metric label="Evidence" value={counts.evidence} />
        <Metric label="Entities" value={counts.entities} />
        <Metric label="Reasoning" value={counts.reasoning_sessions} />
        <Metric label="Pending Execution" value={counts.pending_execution} />
      </div>

      <div className="mt-5 flex flex-col gap-3 border border-border bg-background px-4 py-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2 text-sm">
          <ShieldCheck className="h-4 w-4 text-confidence" />
          <span className="capitalize">
            {health.status.replaceAll("_", " ")}
          </span>
        </div>
        <div className="text-sm text-muted-foreground">{health.summary}</div>
      </div>
    </section>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div className="interactive-card border border-confidence/40 bg-confidence/10 p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-confidence">{value}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="interactive-card border border-border bg-background p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
    </div>
  );
}
