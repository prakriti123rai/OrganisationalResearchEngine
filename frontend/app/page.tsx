"use client";

import "@xyflow/react/dist/style.css";

import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import {
  BarChart3,
  Brain,
  ClipboardCheck,
  CircleAlert,
  Database,
  FileCode2,
  FileText,
  Gauge,
  Network,
  RefreshCw,
  Search,
} from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import {
  ActionCard,
  type SuggestedAction,
} from "../components/actions/ActionCard";
import { ApprovalPanel } from "../components/actions/ApprovalPanel";
import {
  ArtifactViewer,
  type ExecutionRecord,
} from "../components/execution/ArtifactViewer";
import { ExecutionPanel } from "../components/execution/ExecutionPanel";
import { ExecutionTimeline } from "../components/execution/ExecutionTimeline";
import { Timeline, type TraceStage } from "../components/reasoning/Timeline";
import {
  ImpactSummary,
  type ImpactSummaryData,
} from "../components/impact/ImpactSummary";
import type { ImpactEvidence } from "../components/impact/RiskCard";

type View =
  | "dashboard"
  | "evidence"
  | "graph"
  | "reasoning"
  | "impact"
  | "actions"
  | "execution";

type EvidenceRecord = {
  id: string;
  evidence_type: string;
  source: string;
  source_reference: string;
  title: string;
  summary: string;
  timestamp: string;
  referenced_entity_ids: string[];
  supported_relationship_ids: string[];
  supported_signal_ids: string[];
  supported_assumption_ids: string[];
};

type GraphNodeRecord = {
  id: string;
  entity_type: string;
  label: string;
  display_name: string;
  description: string | null;
  status: string;
  supporting_evidence_ids: string[];
};

type GraphEdgeRecord = {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: string;
  graph_relationship_type: string;
  provenance: string;
  strength: string;
  active: boolean;
  supporting_evidence_ids: string[];
  supporting_signal_ids: string[];
};

type OrganizationalGraph = {
  organization_id: string;
  nodes: GraphNodeRecord[];
  edges: GraphEdgeRecord[];
  node_count: number;
  edge_count: number;
};

type ReasoningResult = {
  schema_version: string;
  answer: string;
  model: string;
  provider: string;
  impact_level: string;
  confidence: string;
  findings: {
    id: string;
    title: string;
    summary: string;
    impact: string;
    confidence: string;
    entity_ids: string[];
    evidence_ids: string[];
    signal_ids: string[];
    assumption_ids: string[];
  }[];
  hypotheses: {
    id: string;
    statement: string;
    status: string;
    confidence: string;
    evidence_ids: string[];
    assumption_ids: string[];
  }[];
  recommended_actions: string[];
  impacted_entity_ids: string[];
  primary_evidence_ids: string[];
  metadata: Record<string, string | number | boolean | null>;
};

type ReasoningTrace = {
  organization_id: string;
  stages: TraceStage[];
  result: ReasoningResult;
  metadata: Record<string, string | number | boolean | null>;
};

type ActionPlan = {
  organization_id: string;
  reasoning_session_id: string;
  actions: SuggestedAction[];
};

type ExecutionHistory = {
  organization_id: string;
  executions: ExecutionRecord[];
};

const organizationId = "org-demo-apex";
const reasoningSessionId = "reasoning-demo-pr-482";
const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const navigation = [
  { id: "dashboard" as const, name: "Dashboard", icon: BarChart3 },
  { id: "evidence" as const, name: "Evidence", icon: FileText },
  { id: "graph" as const, name: "Graph", icon: Network },
  { id: "reasoning" as const, name: "Reasoning", icon: Brain },
  { id: "impact" as const, name: "Impact", icon: Gauge },
  { id: "actions" as const, name: "Actions", icon: ClipboardCheck },
  { id: "execution" as const, name: "Execution", icon: FileCode2 },
];

const nodeTypeOrder = [
  "organization",
  "team",
  "person",
  "repository",
  "pull_request",
  "service",
  "feature",
  "external_dependency",
  "rfc",
  "runbook",
  "incident",
  "deployment",
  "document",
];

const nodeColors: Record<string, string> = {
  organization: "#60a5fa",
  team: "#38bdf8",
  person: "#a78bfa",
  repository: "#f59e0b",
  pull_request: "#fb7185",
  service: "#34d399",
  feature: "#facc15",
  external_dependency: "#f97316",
  rfc: "#c084fc",
  runbook: "#2dd4bf",
  incident: "#f87171",
  deployment: "#22c55e",
  document: "#94a3b8",
};

function apiUrl(path: string) {
  return `${apiBaseUrl}${path}`;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

function titleCase(value: string) {
  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function countBy<T>(items: T[], getKey: (item: T) => string) {
  return items.reduce<Record<string, number>>((counts, item) => {
    const key = getKey(item);
    counts[key] = (counts[key] ?? 0) + 1;
    return counts;
  }, {});
}

export default function Home() {
  const [activeView, setActiveView] = useState<View>("dashboard");
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [graph, setGraph] = useState<OrganizationalGraph | null>(null);
  const [reasoningTrace, setReasoningTrace] = useState<ReasoningTrace | null>(
    null,
  );
  const [actions, setActions] = useState<SuggestedAction[]>([]);
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [busyActionId, setBusyActionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const evidenceResult = await fetchJson<EvidenceRecord[]>(
        `/organizations/${organizationId}/evidence?limit=200`,
      );
      await fetchJson(`/organizations/${organizationId}/graph/sync`, {
        method: "POST",
      });
      await fetchJson(
        `/organizations/${organizationId}/reasoning-sessions/${reasoningSessionId}/run`,
        {
          method: "POST",
          body: JSON.stringify({ graph_depth: 2 }),
          headers: {
            "Content-Type": "application/json",
          },
        },
      );
      const graphResult = await fetchJson<OrganizationalGraph>(
        `/organizations/${organizationId}/graph/neo4j`,
      );
      const traceResult = await fetchJson<ReasoningTrace>(
        `/reason/${reasoningSessionId}?organization_id=${organizationId}&graph_depth=2`,
      );
      const actionPlan = await fetchJson<ActionPlan>("/actions/generate", {
        method: "POST",
        body: JSON.stringify({
          organization_id: organizationId,
          reasoning_session_id: reasoningSessionId,
        }),
        headers: {
          "Content-Type": "application/json",
        },
      });
      const executionHistory = await fetchJson<ExecutionHistory>(
        `/execution/history?organization_id=${organizationId}`,
      );
      setEvidence(evidenceResult);
      setGraph(graphResult);
      setReasoningTrace(traceResult);
      setActions(actionPlan.actions);
      setExecutions(executionHistory.executions);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Unable to load ORE data.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function approveAction(action: SuggestedAction) {
    await updateActionStatus(action, "approve");
  }

  async function rejectAction(action: SuggestedAction) {
    await updateActionStatus(action, "reject");
  }

  async function updateActionStatus(
    action: SuggestedAction,
    decision: "approve" | "reject",
  ) {
    setBusyActionId(action.id);
    setError(null);
    try {
      const updated = await fetchJson<SuggestedAction>(
        `/actions/${action.id}/${decision}`,
        {
          method: "POST",
        },
      );
      setActions((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      if (decision === "approve") {
        await refreshExecutions();
      }
    } catch (actionError) {
      setError(
        actionError instanceof Error
          ? actionError.message
          : "Unable to update action status.",
      );
    } finally {
      setBusyActionId(null);
    }
  }

  async function saveAction(
    action: SuggestedAction,
    changes: {
      title: string;
      description: string;
      artifact_preview: string;
    },
  ) {
    setBusyActionId(action.id);
    setError(null);
    try {
      const updated = await fetchJson<SuggestedAction>(
        `/actions/${action.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            organization_id: organizationId,
            ...changes,
          }),
          headers: {
            "Content-Type": "application/json",
          },
        },
      );
      setActions((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch (actionError) {
      setError(
        actionError instanceof Error
          ? actionError.message
          : "Unable to save action.",
      );
    } finally {
      setBusyActionId(null);
    }
  }

  async function startExecution(action: SuggestedAction) {
    setBusyActionId(action.id);
    setError(null);
    try {
      await fetchJson<ExecutionRecord>("/execution/start", {
        method: "POST",
        body: JSON.stringify({
          organization_id: organizationId,
          action_id: action.id,
        }),
        headers: {
          "Content-Type": "application/json",
        },
      });
      await refreshExecutions();
      setActions((current) =>
        current.map((item) =>
          item.id === action.id ? { ...item, status: "executed" } : item,
        ),
      );
    } catch (executionError) {
      setError(
        executionError instanceof Error
          ? executionError.message
          : "Unable to start execution.",
      );
    } finally {
      setBusyActionId(null);
    }
  }

  async function refreshExecutions() {
    const executionHistory = await fetchJson<ExecutionHistory>(
      `/execution/history?organization_id=${organizationId}`,
    );
    setExecutions(executionHistory.executions);
  }

  async function syncGraph() {
    setSyncing(true);
    setError(null);
    try {
      await fetchJson(`/organizations/${organizationId}/graph/sync`, {
        method: "POST",
      });
      const graphResult = await fetchJson<OrganizationalGraph>(
        `/organizations/${organizationId}/graph/neo4j`,
      );
      setGraph(graphResult);
    } catch (syncError) {
      setError(
        syncError instanceof Error
          ? syncError.message
          : "Unable to sync Neo4j graph.",
      );
    } finally {
      setSyncing(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  return (
    <main className="flex min-h-screen bg-background text-foreground">
      <aside className="flex w-64 shrink-0 flex-col border-r border-border bg-muted px-4 py-5">
        <div className="mb-8">
          <div className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">
            ORE
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            Organizational Reasoning Engine
          </div>
        </div>
        <nav className="space-y-1" aria-label="Primary navigation">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = activeView === item.id;
            return (
              <button
                key={item.id}
                className={[
                  "flex h-10 w-full items-center gap-3 rounded-md px-3 text-left text-sm transition",
                  active
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                ].join(" ")}
                onClick={() => setActiveView(item.id)}
                type="button"
              >
                <Icon aria-hidden="true" className="h-4 w-4" />
                <span>{item.name}</span>
              </button>
            );
          })}
        </nav>

        <div className="mt-auto border-t border-border pt-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-confidence" />
            <span>{organizationId}</span>
          </div>
          <div className="mt-2">Backend API: {apiBaseUrl}</div>
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col px-8 py-7">
        <header className="flex items-start justify-between gap-6 border-b border-border pb-6">
          <div>
            <div className="text-sm text-muted-foreground">
              {activeView === "actions"
                ? "Milestone 10"
                : activeView === "execution"
                  ? "Milestone 11"
                  : activeView === "impact"
                    ? "Milestone 9"
                    : "Milestone 8"}
            </div>
            <h1 className="mt-2 text-2xl font-semibold">
              {activeView === "dashboard" && "Organizational Dashboard"}
              {activeView === "evidence" && "Evidence Explorer"}
              {activeView === "graph" && "Organizational Graph"}
              {activeView === "reasoning" && "Reasoning Workspace"}
              {activeView === "impact" && "Impact Report"}
              {activeView === "actions" && "Suggested Actions"}
              {activeView === "execution" && "Execution Center"}
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
              {activeView === "execution"
                ? "Approved actions converted into generated engineering artifacts with execution history."
                : activeView === "actions"
                  ? "Generated engineering actions with human approval controls before Codex execution."
                  : activeView === "reasoning" || activeView === "impact"
                    ? "Evidence-backed reasoning trace for the seeded pre-merge analysis."
                    : "Live demo data from the seeded organization, evidence service, and Neo4j-backed organizational graph."}
            </p>
          </div>
          <button
            className="inline-flex h-10 items-center gap-2 rounded-md border border-border px-3 text-sm text-muted-foreground transition hover:bg-accent hover:text-accent-foreground"
            onClick={() => void loadData()}
            type="button"
          >
            <RefreshCw aria-hidden="true" className="h-4 w-4" />
            Refresh
          </button>
        </header>

        {error && (
          <div className="mt-5 flex items-center gap-3 border border-risk/50 bg-risk/10 px-4 py-3 text-sm text-risk">
            <CircleAlert aria-hidden="true" className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="grid flex-1 place-items-center text-sm text-muted-foreground">
            Collecting evidence, expanding relationships, and activating
            signals...
          </div>
        ) : (
          <div className="min-h-0 flex-1 py-6">
            {activeView === "dashboard" && (
              <Dashboard evidence={evidence} graph={graph} />
            )}
            {activeView === "evidence" && (
              <EvidenceExplorer evidence={evidence} />
            )}
            {activeView === "graph" && (
              <GraphExplorer
                graph={graph}
                syncing={syncing}
                onSync={() => void syncGraph()}
              />
            )}
            {activeView === "reasoning" && (
              <ReasoningWorkspace evidence={evidence} trace={reasoningTrace} />
            )}
            {activeView === "impact" && (
              <ImpactReport
                evidence={evidence}
                graph={graph}
                trace={reasoningTrace}
              />
            )}
            {activeView === "actions" && (
              <SuggestedActions
                actions={actions}
                busyActionId={busyActionId}
                onApprove={approveAction}
                onReject={rejectAction}
                onSave={saveAction}
              />
            )}
            {activeView === "execution" && (
              <ExecutionCenter
                actions={actions}
                busyActionId={busyActionId}
                executions={executions}
                onStartExecution={startExecution}
              />
            )}
          </div>
        )}
      </section>
    </main>
  );
}

function ExecutionCenter({
  actions,
  busyActionId,
  executions,
  onStartExecution,
}: {
  actions: SuggestedAction[];
  busyActionId: string | null;
  executions: ExecutionRecord[];
  onStartExecution: (action: SuggestedAction) => void;
}) {
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(
    null,
  );
  const selectedExecution =
    executions.find((execution) => execution.id === selectedExecutionId) ??
    executions[0] ??
    null;

  if (actions.length === 0) {
    return (
      <div className="grid h-[calc(100vh-190px)] place-items-center border border-border bg-muted text-sm text-muted-foreground">
        Preparing approved actions for Codex artifact generation...
      </div>
    );
  }

  return (
    <div className="grid h-[calc(100vh-190px)] grid-cols-[1fr_420px] gap-5">
      <div className="min-h-0 space-y-5">
        <ExecutionTimeline execution={selectedExecution} />
        <ExecutionPanel
          actions={actions}
          busyActionId={busyActionId}
          executions={executions}
          onSelectExecution={setSelectedExecutionId}
          onStartExecution={onStartExecution}
          selectedExecutionId={selectedExecution?.id ?? null}
        />
      </div>
      <ArtifactViewer execution={selectedExecution} />
    </div>
  );
}

function SuggestedActions({
  actions,
  busyActionId,
  onApprove,
  onReject,
  onSave,
}: {
  actions: SuggestedAction[];
  busyActionId: string | null;
  onApprove: (action: SuggestedAction) => void;
  onReject: (action: SuggestedAction) => void;
  onSave: (
    action: SuggestedAction,
    changes: {
      title: string;
      description: string;
      artifact_preview: string;
    },
  ) => void;
}) {
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null);
  const selectedAction =
    actions.find((action) => action.id === selectedActionId) ??
    actions[0] ??
    null;
  const statusCounts = countBy(actions, (action) => action.status);

  if (actions.length === 0) {
    return (
      <div className="grid h-[calc(100vh-190px)] place-items-center border border-border bg-muted text-sm text-muted-foreground">
        Preparing safe actions from the reasoning report...
      </div>
    );
  }

  return (
    <div className="grid h-[calc(100vh-190px)] grid-cols-[1fr_420px] gap-5">
      <section className="min-h-0 overflow-y-auto border border-border bg-background p-5">
        <div className="grid grid-cols-4 gap-3">
          <TraceMetric label="Generated" value={actions.length} />
          <TraceMetric label="Proposed" value={statusCounts.proposed ?? 0} />
          <TraceMetric label="Approved" value={statusCounts.approved ?? 0} />
          <TraceMetric label="Rejected" value={statusCounts.rejected ?? 0} />
        </div>

        <section className="mt-5 border border-border bg-muted p-5">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold">Generated Actions</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                ORE converts the impact report into human-approved engineering
                work items. Approved actions flow into the Execution Center for
                generated artifacts.
              </p>
            </div>
            <span className="shrink-0 border border-confidence/40 bg-confidence/10 px-3 py-2 text-xs text-confidence">
              Confidence visible
            </span>
          </div>
          <div className="mt-4 grid gap-3">
            {actions.map((action) => (
              <ActionCard
                action={action}
                active={selectedAction?.id === action.id}
                key={action.id}
                onSelect={(nextAction) => setSelectedActionId(nextAction.id)}
              />
            ))}
          </div>
        </section>
      </section>

      <ApprovalPanel
        action={selectedAction}
        busyActionId={busyActionId}
        onApprove={onApprove}
        onReject={onReject}
        onSave={onSave}
      />
    </div>
  );
}

function ImpactReport({
  evidence,
  graph,
  trace,
}: {
  evidence: EvidenceRecord[];
  graph: OrganizationalGraph | null;
  trace: ReasoningTrace | null;
}) {
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(
    null,
  );

  const report = useMemo(
    () => buildImpactReport(trace, evidence, graph, selectedEvidenceId),
    [evidence, graph, selectedEvidenceId, trace],
  );

  if (!trace || !report) {
    return (
      <div className="grid h-[calc(100vh-190px)] place-items-center border border-border bg-muted text-sm text-muted-foreground">
        Predicting impacts, ranking affected services, and linking evidence...
      </div>
    );
  }

  return (
    <ImpactSummary onSelectEvidence={setSelectedEvidenceId} report={report} />
  );
}

function ReasoningWorkspace({
  evidence,
  trace,
}: {
  evidence: EvidenceRecord[];
  trace: ReasoningTrace | null;
}) {
  const [activeEvidenceId, setActiveEvidenceId] = useState<string | null>(null);
  const activeEvidence =
    evidence.find((item) => item.id === activeEvidenceId) ??
    evidence[0] ??
    null;

  if (!trace) {
    return (
      <div className="grid h-[calc(100vh-190px)] place-items-center border border-border bg-muted text-sm text-muted-foreground">
        Collecting evidence, expanding graph, and preparing reasoning trace...
      </div>
    );
  }

  return (
    <div className="grid h-[calc(100vh-190px)] grid-cols-[1fr_360px] gap-5">
      <section className="min-h-0 border border-border bg-background p-5">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">
              Pre-Merge Organizational Reasoning
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {trace.result.answer}
            </p>
          </div>
          <div className="shrink-0 border border-confidence/40 bg-confidence/10 px-3 py-2 text-right">
            <div className="text-xs text-muted-foreground">Confidence</div>
            <div className="mt-1 text-sm font-semibold text-confidence">
              {trace.result.confidence}
            </div>
          </div>
        </div>
        <Timeline
          activeEvidenceId={activeEvidenceId}
          onSelectEvidence={setActiveEvidenceId}
          stages={trace.stages}
        />
      </section>

      <aside className="min-h-0 overflow-y-auto border border-border bg-muted p-4">
        <div className="grid grid-cols-2 gap-3">
          <TraceMetric label="Stages" value={trace.stages.length} />
          <TraceMetric label="Findings" value={trace.result.findings.length} />
          <TraceMetric
            label="Hypotheses"
            value={trace.result.hypotheses.length}
          />
          <TraceMetric
            label="Actions"
            value={trace.result.recommended_actions.length}
          />
        </div>

        <section className="mt-5 border border-border bg-background p-4">
          <h2 className="text-sm font-semibold">Predicted Impact</h2>
          <div className="mt-3 space-y-3">
            {trace.result.findings.map((finding) => (
              <article
                className="border border-border bg-muted p-3"
                key={finding.id}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="text-sm font-semibold">{finding.title}</div>
                  <span className="text-xs text-risk">{finding.impact}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-muted-foreground">
                  {finding.summary}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-5 border border-border bg-background p-4">
          <h2 className="text-sm font-semibold">Selected Evidence</h2>
          {activeEvidence ? (
            <article className="mt-3">
              <div className="text-sm font-semibold">
                {activeEvidence.title}
              </div>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">
                {activeEvidence.summary}
              </p>
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                <Pill>{activeEvidence.source}</Pill>
                <Pill>{titleCase(activeEvidence.evidence_type)}</Pill>
              </div>
            </article>
          ) : (
            <p className="mt-3 text-xs text-muted-foreground">
              Select an evidence chip in the timeline.
            </p>
          )}
        </section>

        <section className="mt-5 border border-border bg-background p-4">
          <h2 className="text-sm font-semibold">Planned Actions</h2>
          <div className="mt-3 space-y-2">
            {trace.result.recommended_actions.map((action) => (
              <div
                className="border border-border bg-muted px-3 py-2 text-xs leading-5 text-muted-foreground"
                key={action}
              >
                {action}
              </div>
            ))}
          </div>
        </section>
      </aside>
    </div>
  );
}

function buildImpactReport(
  trace: ReasoningTrace | null,
  evidence: EvidenceRecord[],
  graph: OrganizationalGraph | null,
  selectedEvidenceId: string | null,
): ImpactSummaryData | null {
  if (!trace) {
    return null;
  }

  const evidenceById = new Map(evidence.map((item) => [item.id, item]));
  const nodesById = new Map(
    (graph?.nodes ?? []).map((node) => [node.id, node]),
  );
  const impactedEntityIds = new Set(trace.result.impacted_entity_ids);
  const findingEntityIds = trace.result.findings.flatMap(
    (finding) => finding.entity_ids,
  );
  findingEntityIds.forEach((entityId) => impactedEntityIds.add(entityId));
  (graph?.edges ?? [])
    .filter(
      (edge) =>
        edge.relationship_type === "affects" &&
        trace.result.impacted_entity_ids.includes(edge.target_entity_id),
    )
    .forEach((edge) => impactedEntityIds.add(edge.target_entity_id));

  const services = Array.from(impactedEntityIds)
    .map((entityId) => nodesById.get(entityId))
    .filter((node): node is GraphNodeRecord => node?.entity_type === "service")
    .map((service) => {
      const directEdges =
        graph?.edges.filter(
          (edge) =>
            edge.source_entity_id === service.id ||
            edge.target_entity_id === service.id,
        ) ?? [];
      const ownerIds = directEdges
        .filter(
          (edge) =>
            ["owns", "maintains"].includes(edge.relationship_type) &&
            edge.target_entity_id === service.id,
        )
        .map((edge) => edge.source_entity_id);
      const owners = ownerIds
        .map((ownerId) => nodesById.get(ownerId)?.display_name)
        .filter((owner): owner is string => Boolean(owner));
      const evidenceIds = unique([
        ...service.supporting_evidence_ids,
        ...directEdges.flatMap((edge) => edge.supporting_evidence_ids),
        ...trace.result.findings.flatMap((finding) =>
          finding.entity_ids.includes(service.id) ? finding.evidence_ids : [],
        ),
      ]);
      const serviceFindings = trace.result.findings.filter((finding) =>
        finding.entity_ids.includes(service.id),
      );
      const highestRisk =
        serviceFindings.find((finding) => finding.impact === "high")?.impact ??
        serviceFindings[0]?.impact ??
        trace.result.impact_level;

      return {
        id: service.id,
        name: service.display_name,
        description: service.description,
        riskLevel: highestRisk,
        confidence: serviceFindings[0]?.confidence ?? trace.result.confidence,
        owners,
        evidenceIds,
      };
    });

  const reportText = [
    trace.result.answer,
    ...trace.result.findings.map((finding) => finding.summary),
    ...trace.result.recommended_actions,
  ]
    .join(" ")
    .toLowerCase();
  const affectedTeams = unique([
    ...services.flatMap((service) => service.owners),
    ...Array.from(impactedEntityIds)
      .map((entityId) => nodesById.get(entityId))
      .filter((node): node is GraphNodeRecord => node?.entity_type === "team")
      .map((team) => team.display_name),
    ...(graph?.nodes ?? [])
      .filter(
        (node) =>
          node.entity_type === "team" &&
          reportText.includes(node.display_name.toLowerCase()),
      )
      .map((team) => team.display_name),
  ]);
  const impactStage = trace.stages.find(
    (stage) => stage.id === "predicting-impacts",
  );
  const actionStage = trace.stages.find(
    (stage) => stage.id === "planning-actions",
  );
  const riskTimeline = [
    impactStage?.summary ?? trace.result.answer,
    ...trace.result.findings.map((finding) => finding.summary),
    actionStage?.summary ??
      `${trace.result.recommended_actions.length} actions planned.`,
  ];
  const toImpactEvidence = (evidenceId: string): ImpactEvidence | null => {
    const item = evidenceById.get(evidenceId);
    if (!item) {
      return null;
    }
    return {
      id: item.id,
      title: item.title,
      summary: item.summary,
      source: item.source_reference,
    };
  };
  const primaryEvidence = trace.result.primary_evidence_ids
    .map(toImpactEvidence)
    .filter((item): item is ImpactEvidence => Boolean(item));
  const selectedEvidence =
    (selectedEvidenceId ? toImpactEvidence(selectedEvidenceId) : null) ??
    primaryEvidence[0] ??
    null;

  return {
    answer: trace.result.answer,
    impactLevel: trace.result.impact_level,
    confidence: trace.result.confidence,
    affectedTeams:
      affectedTeams.length > 0 ? affectedTeams : ["Payments", "SRE"],
    services,
    risks: trace.result.findings.map((finding) => ({
      id: finding.id,
      title: finding.title,
      summary: finding.summary,
      impact: finding.impact,
      confidence: finding.confidence,
      evidence: finding.evidence_ids
        .map(toImpactEvidence)
        .filter((item): item is ImpactEvidence => Boolean(item)),
    })),
    riskTimeline,
    selectedEvidence,
    primaryEvidence,
  };
}

function unique(values: string[]) {
  return Array.from(new Set(values.filter(Boolean)));
}

function Dashboard({
  evidence,
  graph,
}: {
  evidence: EvidenceRecord[];
  graph: OrganizationalGraph | null;
}) {
  const evidenceBySource = countBy(evidence, (item) => item.source);
  const nodeTypeCounts = countBy(
    graph?.nodes ?? [],
    (node) => node.entity_type,
  );
  const riskEvidence = evidence.filter(
    (item) =>
      item.summary.toLowerCase().includes("risk") ||
      item.title.toLowerCase().includes("risk") ||
      item.supported_signal_ids.some((signal) => signal.includes("risk")),
  );
  const affectedEdges =
    graph?.edges.filter((edge) => edge.relationship_type === "affects")
      .length ?? 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Metric label="Evidence Records" value={evidence.length} />
        <Metric label="Graph Nodes" value={graph?.node_count ?? 0} />
        <Metric label="Graph Edges" value={graph?.edge_count ?? 0} />
        <Metric label="PR Impact Edges" value={affectedEdges} tone="risk" />
      </div>

      <div className="grid grid-cols-[1.2fr_0.8fr] gap-6">
        <section className="border border-border bg-muted p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Recent Evidence</h2>
            <span className="text-xs text-muted-foreground">
              Seeded demo dataset
            </span>
          </div>
          <div className="space-y-3">
            {evidence.slice(0, 5).map((item) => (
              <article
                key={item.id}
                className="border border-border bg-background p-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-sm font-semibold">{item.title}</h3>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {formatDate(item.timestamp)}
                  </span>
                </div>
                <p className="mt-2 text-sm leading-5 text-muted-foreground">
                  {item.summary}
                </p>
                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  <Pill>{titleCase(item.evidence_type)}</Pill>
                  <Pill>{item.source}</Pill>
                  <Pill>{item.referenced_entity_ids.length} entities</Pill>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="space-y-6">
          <div className="border border-border bg-muted p-5">
            <h2 className="text-lg font-semibold">Evidence Sources</h2>
            <div className="mt-4 space-y-3">
              {Object.entries(evidenceBySource).map(([source, count]) => (
                <Bar
                  key={source}
                  label={source}
                  value={count}
                  max={evidence.length}
                />
              ))}
            </div>
          </div>

          <div className="border border-border bg-muted p-5">
            <h2 className="text-lg font-semibold">Graph Composition</h2>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              {Object.entries(nodeTypeCounts).map(([type, count]) => (
                <div
                  key={type}
                  className="border border-border bg-background p-3"
                >
                  <div className="text-muted-foreground">{titleCase(type)}</div>
                  <div className="mt-1 text-xl font-semibold">{count}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="border border-risk/40 bg-risk/10 p-5">
            <h2 className="text-lg font-semibold text-risk">
              Risk Signals in Evidence
            </h2>
            <div className="mt-2 text-3xl font-semibold">
              {riskEvidence.length}
            </div>
            <p className="mt-2 text-sm leading-5 text-muted-foreground">
              Records mentioning checkout risk, hidden dependencies, or reviewer
              concentration.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}

function EvidenceExplorer({ evidence }: { evidence: EvidenceRecord[] }) {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("all");
  const [type, setType] = useState("all");

  const sources = useMemo(
    () => [
      "all",
      ...Array.from(new Set(evidence.map((item) => item.source))).sort(),
    ],
    [evidence],
  );
  const types = useMemo(
    () => [
      "all",
      ...Array.from(new Set(evidence.map((item) => item.evidence_type))).sort(),
    ],
    [evidence],
  );
  const filtered = evidence.filter((item) => {
    const searchText =
      `${item.title} ${item.summary} ${item.source_reference}`.toLowerCase();
    return (
      (source === "all" || item.source === source) &&
      (type === "all" || item.evidence_type === type) &&
      searchText.includes(query.toLowerCase())
    );
  });

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-[1fr_180px_220px] gap-3">
        <label className="relative">
          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <input
            className="h-10 w-full border border-border bg-muted pl-9 pr-3 text-sm outline-none focus:border-primary"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search evidence"
            value={query}
          />
        </label>
        <select
          className="h-10 border border-border bg-muted px-3 text-sm outline-none focus:border-primary"
          onChange={(event) => setSource(event.target.value)}
          value={source}
        >
          {sources.map((item) => (
            <option key={item} value={item}>
              {item === "all" ? "All sources" : item}
            </option>
          ))}
        </select>
        <select
          className="h-10 border border-border bg-muted px-3 text-sm outline-none focus:border-primary"
          onChange={(event) => setType(event.target.value)}
          value={type}
        >
          {types.map((item) => (
            <option key={item} value={item}>
              {item === "all" ? "All evidence types" : titleCase(item)}
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-3">
        {filtered.map((item) => (
          <article key={item.id} className="border border-border bg-muted p-4">
            <div className="grid grid-cols-[1fr_auto] gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-base font-semibold">{item.title}</h2>
                  <Pill>{titleCase(item.evidence_type)}</Pill>
                  <Pill>{item.source}</Pill>
                </div>
                <p className="mt-2 text-sm leading-5 text-muted-foreground">
                  {item.summary}
                </p>
              </div>
              <div className="text-right text-xs text-muted-foreground">
                <div>{formatDate(item.timestamp)}</div>
                <div className="mt-1">{item.source_reference}</div>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-4 gap-3 text-xs">
              <EvidenceCount
                label="Entities"
                value={item.referenced_entity_ids.length}
              />
              <EvidenceCount
                label="Relationships"
                value={item.supported_relationship_ids.length}
              />
              <EvidenceCount
                label="Signals"
                value={item.supported_signal_ids.length}
              />
              <EvidenceCount
                label="Assumptions"
                value={item.supported_assumption_ids.length}
              />
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function GraphExplorer({
  graph,
  syncing,
  onSync,
}: {
  graph: OrganizationalGraph | null;
  syncing: boolean;
  onSync: () => void;
}) {
  const { nodes, edges } = useMemo(() => buildFlowGraph(graph), [graph]);
  const highContextEdges = graph?.edges.filter(
    (edge) => edge.supporting_evidence_ids.length > 0,
  );

  return (
    <div className="grid h-[calc(100vh-190px)] grid-cols-[1fr_320px] gap-5">
      <section className="min-h-0 border border-border bg-muted">
        <div className="flex h-12 items-center justify-between border-b border-border px-4">
          <div className="flex items-center gap-3">
            <Network className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold">
              Neo4j Organizational Graph
            </span>
            <Pill>{graph?.node_count ?? 0} nodes</Pill>
            <Pill>{graph?.edge_count ?? 0} edges</Pill>
          </div>
          <button
            className="inline-flex h-8 items-center gap-2 rounded-md border border-border px-3 text-xs text-muted-foreground transition hover:bg-accent hover:text-accent-foreground"
            disabled={syncing}
            onClick={onSync}
            type="button"
          >
            <RefreshCw
              className={["h-3.5 w-3.5", syncing ? "animate-spin" : ""].join(
                " ",
              )}
            />
            Sync Neo4j
          </button>
        </div>
        <div className="h-[calc(100%-48px)]">
          <ReactFlow
            colorMode="dark"
            edges={edges}
            fitView
            maxZoom={1.6}
            minZoom={0.35}
            nodes={nodes}
            nodesDraggable
          >
            <Background color="#334155" gap={22} />
            <Controls />
            <MiniMap
              maskColor="rgba(8, 13, 23, 0.7)"
              nodeColor={(node) => String(node.style?.background ?? "#60a5fa")}
            />
          </ReactFlow>
        </div>
      </section>

      <aside className="min-h-0 overflow-auto border border-border bg-muted p-4">
        <h2 className="text-base font-semibold">Relationship Evidence</h2>
        <p className="mt-2 text-sm leading-5 text-muted-foreground">
          Canonical relationship edges with retained evidence links.
        </p>
        <div className="mt-4 space-y-3">
          {(highContextEdges ?? []).slice(0, 8).map((edge) => (
            <article
              key={edge.id}
              className="border border-border bg-background p-3"
            >
              <div className="text-sm font-semibold">
                {titleCase(edge.relationship_type)}
              </div>
              <div className="mt-1 text-xs text-muted-foreground">
                {edge.source_entity_id} to {edge.target_entity_id}
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                <Pill>{edge.strength}</Pill>
                <Pill>{edge.provenance}</Pill>
                <Pill>{edge.supporting_evidence_ids.length} evidence</Pill>
              </div>
            </article>
          ))}
        </div>
      </aside>
    </div>
  );
}

function buildFlowGraph(graph: OrganizationalGraph | null): {
  nodes: Node[];
  edges: Edge[];
} {
  if (!graph) {
    return { nodes: [], edges: [] };
  }

  const typeCounters = new Map<string, number>();
  const nodes = graph.nodes.map((node) => {
    const order = nodeTypeOrder.includes(node.entity_type)
      ? nodeTypeOrder.indexOf(node.entity_type)
      : nodeTypeOrder.length;
    const row = typeCounters.get(node.entity_type) ?? 0;
    typeCounters.set(node.entity_type, row + 1);
    const column = order % 5;
    const band = Math.floor(order / 5);

    return {
      id: node.id,
      data: {
        label: `${node.display_name}\n${titleCase(node.entity_type)}`,
      },
      position: {
        x: column * 230,
        y: band * 250 + row * 98 + (column % 2) * 26,
      },
      style: {
        width: 180,
        minHeight: 58,
        borderRadius: 6,
        border: "1px solid rgba(148, 163, 184, 0.55)",
        background: nodeColors[node.entity_type] ?? "#64748b",
        color: "#06111f",
        fontSize: 12,
        fontWeight: 700,
        whiteSpace: "pre-line",
      },
    } satisfies Node;
  });

  const edges = graph.edges.map((edge) => ({
    id: edge.id,
    source: edge.source_entity_id,
    target: edge.target_entity_id,
    label: titleCase(edge.relationship_type),
    animated:
      edge.relationship_type === "affects" ||
      edge.relationship_type === "depends_on",
    style: {
      stroke: edge.relationship_type === "affects" ? "#fb7185" : "#93c5fd",
      strokeWidth: edge.strength === "strong" ? 2.5 : 1.5,
    },
    labelStyle: {
      fill: "#dbeafe",
      fontSize: 11,
      fontWeight: 600,
    },
  }));

  return { nodes, edges };
}

function TraceMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-border bg-background p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
    </div>
  );
}

function Metric({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number;
  tone?: "default" | "risk";
}) {
  return (
    <div className="border border-border bg-muted p-4">
      <div className="text-sm text-muted-foreground">{label}</div>
      <div
        className={[
          "mt-2 text-3xl font-semibold",
          tone === "risk" ? "text-risk" : "",
        ].join(" ")}
      >
        {value}
      </div>
    </div>
  );
}

function Pill({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex h-6 items-center rounded-md border border-border bg-accent px-2 text-xs text-muted-foreground">
      {children}
    </span>
  );
}

function EvidenceCount({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-border bg-background px-3 py-2">
      <div className="text-muted-foreground">{label}</div>
      <div className="mt-1 text-sm font-semibold">{value}</div>
    </div>
  );
}

function Bar({
  label,
  value,
  max,
}: {
  label: string;
  value: number;
  max: number;
}) {
  const width = max > 0 ? `${Math.max(8, (value / max) * 100)}%` : "0%";

  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span>{value}</span>
      </div>
      <div className="h-2 bg-background">
        <div className="h-2 bg-primary" style={{ width }} />
      </div>
    </div>
  );
}
