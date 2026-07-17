import { Network } from "lucide-react";

export type AffectedService = {
  id: string;
  name: string;
  description: string | null;
  riskLevel: string;
  confidence: string;
  owners: string[];
  evidenceIds: string[];
};

export type AffectedServicesProps = {
  services: AffectedService[];
  onSelectEvidence: (evidenceId: string) => void;
};

export function AffectedServices({
  services,
  onSelectEvidence,
}: AffectedServicesProps) {
  return (
    <section className="border border-border bg-muted p-5">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Network className="h-4 w-4 text-primary" />
          <h2 className="text-base font-semibold">Affected Services</h2>
        </div>
        <span className="text-xs text-muted-foreground">
          {services.length} services
        </span>
      </div>

      <div className="mt-4 grid gap-3">
        {services.map((service) => (
          <article
            className="border border-border bg-background p-4"
            key={service.id}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <h3 className="text-sm font-semibold">{service.name}</h3>
                {service.description && (
                  <p className="mt-2 text-xs leading-5 text-muted-foreground">
                    {service.description}
                  </p>
                )}
              </div>
              <div className="shrink-0 text-right">
                <div className="text-xs uppercase text-risk">
                  {service.riskLevel}
                </div>
                <div className="mt-1 text-xs text-confidence">
                  {service.confidence}
                </div>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-[1fr_1.2fr] gap-3 text-xs">
              <div className="border border-border bg-muted px-3 py-2">
                <div className="text-muted-foreground">Owners</div>
                <div className="mt-1 font-semibold">
                  {service.owners.length > 0
                    ? service.owners.join(", ")
                    : "Unresolved"}
                </div>
              </div>
              <div className="border border-border bg-muted px-3 py-2">
                <div className="text-muted-foreground">Evidence</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {service.evidenceIds.map((evidenceId) => (
                    <button
                      className="h-6 border border-border bg-accent px-2 text-xs text-muted-foreground transition hover:border-primary hover:text-foreground"
                      key={evidenceId}
                      onClick={() => onSelectEvidence(evidenceId)}
                      type="button"
                    >
                      {evidenceId}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
