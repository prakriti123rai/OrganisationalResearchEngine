import { Network } from "lucide-react";

import type { GraphPreviewData } from "./Dashboard";

const previewColors: Record<string, string> = {
  organization: "#1d4ed8",
  team: "#0f766e",
  person: "#475569",
  repository: "#475569",
  pull_request: "#9f1239",
  service: "#1d4ed8",
  feature: "#0f766e",
  external_dependency: "#475569",
  rfc: "#475569",
  runbook: "#475569",
  incident: "#9f1239",
  deployment: "#0f766e",
};

export function GraphPreview({ graph }: { graph: GraphPreviewData }) {
  const positionedNodes = graph.nodes.map((node, index) => ({
    ...node,
    x: 5 + (index % 4) * 24,
    y: 8 + Math.floor(index / 4) * 25,
  }));
  const nodesById = new Map(positionedNodes.map((node) => [node.id, node]));

  return (
    <section className="polished-panel border p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Network className="h-4 w-4 text-primary" />
          <h2 className="text-base font-semibold">Knowledge Graph Preview</h2>
        </div>
        <div className="text-xs text-muted-foreground">
          {graph.node_count} nodes / {graph.edge_count} edges
        </div>
      </div>

      <div className="relative h-[30rem] overflow-hidden border border-border bg-background/70">
        <svg className="absolute inset-0 h-full w-full" role="img">
          {graph.edges.slice(0, 16).map((edge, index) => {
            const source = nodesById.get(edge.source_entity_id);
            const target = nodesById.get(edge.target_entity_id);
            if (!source || !target) {
              return null;
            }
            return (
              <line
                key={edge.id}
                stroke={
                  edge.relationship_type === "affects" ? "#c2415c" : "#718096"
                }
                strokeWidth={edge.strength === "strong" ? 2 : 1}
                strokeDasharray="5 5"
                style={{
                  animation: `fadeIn 260ms ease-out ${index * 45}ms both`,
                }}
                x1={`${source.x}%`}
                x2={`${target.x}%`}
                y1={`${source.y}%`}
                y2={`${target.y}%`}
              />
            );
          })}
        </svg>
        {positionedNodes.map((node, index) => (
          <div
            className="interactive-card absolute max-w-28 border border-slate-300/30 px-2 py-1 text-xs font-semibold text-slate-100 shadow-[0_8px_18px_rgba(0,0,0,0.2)]"
            key={node.id}
            style={{
              background: previewColors[node.entity_type] ?? "#94a3b8",
              left: `${node.x}%`,
              top: `${node.y}%`,
              animation: `fadeIn 220ms ease-out ${index * 55}ms both`,
            }}
          >
            {node.display_name}
          </div>
        ))}
      </div>
    </section>
  );
}
