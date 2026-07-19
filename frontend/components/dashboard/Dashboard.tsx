import { Activity, GitPullRequest } from "lucide-react";

import { GraphPreview } from "./GraphPreview";
import { OrganizationCard } from "./OrganizationCard";
import { RecentReasoning } from "./RecentReasoning";

export type DashboardData = {
  organization: {
    id: string;
    name: string;
    description: string | null;
    status: string;
    extra_metadata: Record<string, unknown>;
    created_at: string;
    updated_at: string;
  };
  counts: {
    repositories: number;
    users: number;
    pull_requests: number;
    open_pull_requests: number;
    evidence: number;
    entities: number;
    relationships: number;
    reasoning_sessions: number;
    actions: number;
    pending_execution: number;
    completed_executions: number;
  };
  health: {
    status: string;
    health_score: number;
    knowledge_score: number;
    risk_level: string;
    summary: string;
  };
  recent_pull_requests: RecentPullRequest[];
  recent_reasoning: RecentReasoningItem[];
  recent_predictions: RecentPrediction[];
  recent_activity: RecentActivity[];
  graph_preview: GraphPreviewData;
  metadata: Record<string, unknown>;
};

export type RecentPullRequest = {
  id: string;
  title: string;
  repository: string;
  status: string;
  updated_at: string;
};

export type RecentReasoningItem = {
  id: string;
  question: string;
  status: string;
  impact_level: string | null;
  confidence: string | null;
  completed_at: string | null;
  pull_request_title: string | null;
};

export type RecentPrediction = {
  id: string;
  title: string;
  summary: string;
  impact: string;
  confidence: string;
  reasoning_session_id: string;
};

export type RecentActivity = {
  id: string;
  activity_type: string;
  title: string;
  summary: string;
  timestamp: string;
};

export type GraphPreviewData = {
  nodes: GraphPreviewNode[];
  edges: GraphPreviewEdge[];
  node_count: number;
  edge_count: number;
};

export type GraphPreviewNode = {
  id: string;
  entity_type: string;
  display_name: string;
  description: string | null;
};

export type GraphPreviewEdge = {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: string;
  strength: string;
};

export function Dashboard({ dashboard }: { dashboard: DashboardData | null }) {
  if (!dashboard) {
    return (
      <div className="grid h-[calc(100vh-190px)] place-items-center border border-border bg-muted text-sm text-muted-foreground">
        Summarizing organization health, graph coverage, and recent reasoning...
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <OrganizationCard dashboard={dashboard} />

      <div className="grid grid-cols-[1fr_360px] gap-5">
        <div className="space-y-5">
          <RecentReasoning
            predictions={dashboard.recent_predictions}
            reasoning={dashboard.recent_reasoning}
          />
          <GraphPreview graph={dashboard.graph_preview} />
        </div>
        <aside className="space-y-5">
          <PullRequestPanel pullRequests={dashboard.recent_pull_requests} />
          <ActivityPanel activity={dashboard.recent_activity} />
        </aside>
      </div>
    </div>
  );
}

function PullRequestPanel({
  pullRequests,
}: {
  pullRequests: RecentPullRequest[];
}) {
  return (
    <section className="border border-border bg-muted p-5">
      <div className="flex items-center gap-2">
        <GitPullRequest className="h-4 w-4 text-primary" />
        <h2 className="text-base font-semibold">Recent PRs</h2>
      </div>
      <div className="mt-4 space-y-3">
        {pullRequests.map((pullRequest) => (
          <article
            className="border border-border bg-background p-3"
            key={pullRequest.id}
          >
            <div className="text-sm font-semibold">{pullRequest.title}</div>
            <div className="mt-2 flex items-center justify-between gap-3 text-xs text-muted-foreground">
              <span>{pullRequest.repository}</span>
              <span className="capitalize">{pullRequest.status}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ActivityPanel({ activity }: { activity: RecentActivity[] }) {
  return (
    <section className="border border-border bg-muted p-5">
      <div className="flex items-center gap-2">
        <Activity className="h-4 w-4 text-confidence" />
        <h2 className="text-base font-semibold">Recent Activity</h2>
      </div>
      <div className="mt-4 space-y-3">
        {activity.map((item) => (
          <article
            className="border border-border bg-background p-3"
            key={item.id}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="text-sm font-semibold">{item.title}</div>
              <span className="shrink-0 text-xs capitalize text-muted-foreground">
                {item.activity_type}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">
              {item.summary}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
