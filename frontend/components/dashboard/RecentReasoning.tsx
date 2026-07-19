import { Brain, GitPullRequest, Gauge } from "lucide-react";
import type { ReactNode } from "react";

import type { RecentPrediction, RecentReasoningItem } from "./Dashboard";

export function RecentReasoning({
  predictions,
  reasoning,
}: {
  predictions: RecentPrediction[];
  reasoning: RecentReasoningItem[];
}) {
  return (
    <section className="grid grid-cols-2 gap-5">
      <div className="border border-border bg-muted p-5">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-primary" />
          <h2 className="text-base font-semibold">Recent Reasoning</h2>
        </div>
        <div className="mt-4 space-y-3">
          {reasoning.map((item) => (
            <article
              className="border border-border bg-background p-4"
              key={item.id}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold">
                    {item.pull_request_title ?? item.question}
                  </h3>
                  <p className="mt-2 text-xs leading-5 text-muted-foreground">
                    {item.question}
                  </p>
                </div>
                <span className="shrink-0 text-xs capitalize text-confidence">
                  {item.confidence ?? item.status}
                </span>
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                <Pill>{item.status}</Pill>
                {item.impact_level && <Pill>{item.impact_level} impact</Pill>}
              </div>
            </article>
          ))}
        </div>
      </div>

      <div className="border border-border bg-muted p-5">
        <div className="flex items-center gap-2">
          <Gauge className="h-4 w-4 text-risk" />
          <h2 className="text-base font-semibold">Recent Predictions</h2>
        </div>
        <div className="mt-4 space-y-3">
          {predictions.map((prediction) => (
            <article
              className="border border-border bg-background p-4"
              key={prediction.id}
            >
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-sm font-semibold">{prediction.title}</h3>
                <span className="shrink-0 text-xs text-risk">
                  {prediction.impact}
                </span>
              </div>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">
                {prediction.summary}
              </p>
              <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                <GitPullRequest className="h-3.5 w-3.5" />
                {prediction.confidence} confidence
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function Pill({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex h-6 items-center border border-border bg-accent px-2 text-muted-foreground">
      {children}
    </span>
  );
}
