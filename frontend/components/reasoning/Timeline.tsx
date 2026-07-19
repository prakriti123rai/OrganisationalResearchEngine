import { useEffect, useMemo, useState } from "react";

import { ConflictCard } from "./ConflictCard";
import { EvidenceCard } from "./EvidenceCard";
import { HypothesisCard } from "./HypothesisCard";
import { PredictionCard } from "./PredictionCard";
import { SignalCard } from "./SignalCard";

export type TraceArtifact = {
  id: string;
  title: string;
  summary: string;
  artifact_type: string;
  status: string;
  confidence: string | null;
  evidence_ids: string[];
  relationship_ids: string[];
  signal_ids: string[];
  assumption_ids: string[];
  hypothesis_ids: string[];
};

export type TraceStage = {
  id: string;
  order: number;
  title: string;
  summary: string;
  status: string;
  artifacts: TraceArtifact[];
};

export type TimelineProps = {
  stages: TraceStage[];
  activeEvidenceId: string | null;
  onSelectEvidence: (evidenceId: string) => void;
};

export function Timeline({
  stages,
  activeEvidenceId,
  onSelectEvidence,
}: TimelineProps) {
  const orderedStages = useMemo(
    () => [...stages].sort((left, right) => left.order - right.order),
    [stages],
  );
  const [visibleCount, setVisibleCount] = useState(1);

  useEffect(() => {
    setVisibleCount(1);
    if (orderedStages.length <= 1) {
      return;
    }
    const interval = window.setInterval(() => {
      setVisibleCount((current) => {
        if (current >= orderedStages.length) {
          window.clearInterval(interval);
          return current;
        }
        return current + 1;
      });
    }, 360);
    return () => window.clearInterval(interval);
  }, [orderedStages.length]);

  const progress =
    orderedStages.length === 0
      ? 0
      : Math.round((visibleCount / orderedStages.length) * 100);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto pr-2">
      <div className="sticky top-0 z-10 mb-4 border border-border bg-background/95 p-3 backdrop-blur">
        <div className="flex items-center justify-between gap-4 text-xs">
          <span className="font-semibold text-foreground">
            Reasoning trace reveal
          </span>
          <span className="text-confidence">{progress}%</span>
        </div>
        <div className="mt-3 h-1.5 overflow-hidden bg-muted">
          <div
            className="h-full bg-confidence transition-[width] duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      <div className="relative space-y-4">
        <div className="absolute bottom-0 left-4 top-0 w-px bg-border" />
        {orderedStages.slice(0, visibleCount).map((stage) => (
          <section
            className="interactive-card polished-panel relative ml-10 border p-4 motion-safe:animate-[fadeIn_240ms_ease-out]"
            key={stage.id}
          >
            <div className="absolute -left-[31px] top-4 grid h-8 w-8 place-items-center rounded-full border border-primary bg-background text-xs font-semibold text-primary shadow-[0_0_0_4px_hsl(var(--background))]">
              {stage.order}
            </div>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold">{stage.title}</h2>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">
                  {stage.summary}
                </p>
              </div>
              <span className="rounded-md border border-confidence/40 bg-confidence/10 px-2 py-1 text-xs capitalize text-confidence">
                {stage.status}
              </span>
            </div>
            <div className="mt-4 grid gap-3">
              {stage.artifacts.map((artifact) => (
                <TimelineArtifact
                  activeEvidenceId={activeEvidenceId}
                  artifact={artifact}
                  key={artifact.id}
                  onSelectEvidence={onSelectEvidence}
                  stageId={stage.id}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function TimelineArtifact({
  artifact,
  stageId,
  activeEvidenceId,
  onSelectEvidence,
}: {
  artifact: TraceArtifact;
  stageId: string;
  activeEvidenceId: string | null;
  onSelectEvidence: (evidenceId: string) => void;
}) {
  if (artifact.artifact_type === "evidence") {
    return (
      <EvidenceCard
        evidenceIds={artifact.evidence_ids}
        onSelectEvidence={onSelectEvidence}
        summary={artifact.summary}
        title={artifact.title}
      />
    );
  }

  if (artifact.artifact_type === "signal") {
    return (
      <SignalCard
        confidence={artifact.confidence}
        summary={artifact.summary}
        title={artifact.title}
      />
    );
  }

  if (artifact.artifact_type === "hypothesis") {
    return (
      <HypothesisCard
        assumptionIds={artifact.assumption_ids}
        confidence={artifact.confidence}
        evidenceIds={artifact.evidence_ids}
        summary={artifact.summary}
        title={artifact.title}
      />
    );
  }

  if (stageId === "resolving-conflicts") {
    return <ConflictCard summary={artifact.summary} />;
  }

  if (artifact.artifact_type === "prediction") {
    return (
      <PredictionCard
        confidence={artifact.confidence}
        evidenceCount={artifact.evidence_ids.length}
        summary={artifact.summary}
        title={artifact.title}
      />
    );
  }

  return (
    <article
      className={[
        "border border-border bg-background p-3",
        activeEvidenceId && artifact.evidence_ids.includes(activeEvidenceId)
          ? "border-primary"
          : "",
      ].join(" ")}
    >
      <div className="text-sm font-semibold">{artifact.title}</div>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">
        {artifact.summary}
      </p>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
        {artifact.relationship_ids.length > 0 && (
          <span>{artifact.relationship_ids.length} relationships</span>
        )}
        {artifact.evidence_ids.length > 0 && (
          <span>{artifact.evidence_ids.length} evidence</span>
        )}
        {artifact.assumption_ids.length > 0 && (
          <span>{artifact.assumption_ids.length} assumptions</span>
        )}
      </div>
    </article>
  );
}
