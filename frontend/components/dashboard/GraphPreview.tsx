import { Network } from "lucide-react";

import type { GraphPreviewData } from "./Dashboard";

const previewColors: Record<string, string> = {
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
};

export function GraphPreview({ graph }: { graph: GraphPreviewData }) {
  const positionedNodes = graph.nodes.map((node, index) => ({
    ...node,
    x: 8 + (index % 4) * 23,
    y: 12 + Math.floor(index / 4) * 30,
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

      <div className="relative h-72 overflow-hidden border border-border bg-background">
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
                  edge.relationship_type === "affects" ? "#fb7185" : "#64748b"
                }
                strokeWidth={edge.strength === "strong" ? 2 : 1}
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
            className="interactive-card absolute max-w-32 border border-border px-2 py-1 text-xs font-semibold text-background"
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
