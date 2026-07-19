import { Building2, ShieldCheck } from "lucide-react";

import type { DashboardData } from "./Dashboard";

export function OrganizationCard({ dashboard }: { dashboard: DashboardData }) {
  const { organization, health, counts } = dashboard;

  return (
    <section className="border border-border bg-muted p-5">
      <div className="flex items-start justify-between gap-5">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase text-primary">
            <Building2 className="h-4 w-4" />
            Organization Health
          </div>
          <h2 className="mt-3 text-xl font-semibold">{organization.name}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            {organization.description}
          </p>
        </div>
        <div className="grid w-56 grid-cols-2 gap-3 text-right">
          <Score label="Health" value={health.health_score} />
          <Score label="Knowledge" value={health.knowledge_score} />
        </div>
      </div>

      <div className="mt-5 grid grid-cols-5 gap-3">
        <Metric label="Repositories" value={counts.repositories} />
        <Metric label="Evidence" value={counts.evidence} />
        <Metric label="Entities" value={counts.entities} />
        <Metric label="Reasoning" value={counts.reasoning_sessions} />
        <Metric label="Pending Execution" value={counts.pending_execution} />
      </div>

      <div className="mt-5 flex items-center justify-between border border-border bg-background px-4 py-3">
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
    <div className="border border-confidence/40 bg-confidence/10 p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-confidence">{value}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-border bg-background p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
    </div>
  );
}
