import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactFlow, { Background, Controls, MarkerType, type Edge, type Node } from "reactflow";
import dagre from "dagre";
import "reactflow/dist/style.css";
import { api } from "../lib/api";
import type { Launch } from "../lib/types";
import { PageHeader } from "../components/PageHeader";

interface DepRow {
  id: string;
  source_type: string;
  source_id: string;
  target_type: string;
  target_id: string;
  link_type: string;
  notes?: string | null;
}

const LINK_COLOR: Record<string, string> = {
  blocks: "#C8102E",
  references_price: "#165d59",
  informs: "#8A8A8A",
  shares_supply: "#B8740A",
  shares_evidence: "#2F7D4F",
};

function layout(nodes: Node[], edges: Edge[]): { nodes: Node[]; edges: Edge[] } {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "LR", ranksep: 120, nodesep: 40 });
  nodes.forEach((n) => g.setNode(n.id, { width: 200, height: 70 }));
  edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);
  return {
    nodes: nodes.map((n) => {
      const pos = g.node(n.id);
      return { ...n, position: { x: pos.x - 100, y: pos.y - 35 } };
    }),
    edges,
  };
}

export function DependenciesGraph() {
  const { data: launches } = useQuery({ queryKey: ["launches"], queryFn: () => api<Launch[]>("/launches") });
  const { data: deps } = useQuery({ queryKey: ["deps"], queryFn: () => api<DepRow[]>("/dependencies") });

  const flow = useMemo(() => {
    if (!launches || !deps) return { nodes: [], edges: [] };
    const byId = new Map(launches.map((l) => [l.id, l]));
    const referenced = new Set<string>();
    deps.forEach((d) => { referenced.add(d.source_id); referenced.add(d.target_id); });
    const nodes: Node[] = launches
      .filter((l) => referenced.has(l.id) || deps.some((d) => d.source_id === l.id || d.target_id === l.id))
      .map((l) => ({
        id: l.id,
        data: {
          label: (
            <div className="text-left">
              <div className="font-mono text-[10px] uppercase tracking-wider text-mute">{l.launch_code}</div>
              <div className="font-medium text-sm">{l.asset.brand_name}</div>
              <div className="text-xs text-mute-2">{l.country.name}</div>
            </div>
          ),
        },
        position: { x: 0, y: 0 },
        style: {
          border: `2px solid ${l.overall_rag === "Green" ? "#2F7D4F" : l.overall_rag === "Amber" ? "#B8740A" : "#C8102E"}`,
          borderRadius: 8,
          padding: 10,
          background: "white",
          width: 200,
        },
      }));
    // Include any launches with no deps for context
    launches.forEach((l) => {
      if (!nodes.some((n) => n.id === l.id)) {
        nodes.push({
          id: l.id,
          data: { label: <div className="text-xs text-mute"><div className="font-mono">{l.launch_code}</div>{l.asset.brand_name}</div> },
          position: { x: 0, y: 0 },
          style: { border: "1px dashed #D0D0D0", borderRadius: 8, padding: 8, background: "#FAFAFA", width: 200 },
        });
      }
    });
    const edges: Edge[] = deps.map((d) => ({
      id: d.id,
      source: d.source_id,
      target: d.target_id,
      label: d.link_type.replace(/_/g, " "),
      labelStyle: { fontSize: 10, fontFamily: "JetBrains Mono" },
      style: { stroke: LINK_COLOR[d.link_type] ?? "#8A8A8A", strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: LINK_COLOR[d.link_type] ?? "#8A8A8A" },
    }));
    return layout(nodes, edges);
  }, [launches, deps]);

  return (
    <>
      <PageHeader
        eyebrow="Dependencies graph"
        title="Everything connects."
        subtitle="Typed cross-launch dependencies. Edge color encodes link type — red blocks, teal references price, amber shares supply, green shares evidence."
      />
      <div className="px-10 py-6">
        <div className="h-[640px] border border-line rounded-lg bg-paper">
          <ReactFlow nodes={flow.nodes} edges={flow.edges} fitView proOptions={{ hideAttribution: true }}>
            <Background gap={20} color="#E5E5E5" />
            <Controls position="bottom-right" />
          </ReactFlow>
        </div>
        <div className="mt-4 flex items-center gap-4 text-xs font-mono uppercase tracking-wider text-mute">
          {Object.entries(LINK_COLOR).map(([k, v]) => (
            <div key={k} className="flex items-center gap-1.5"><span className="w-3 h-0.5" style={{ background: v }} /> {k.replace(/_/g, " ")}</div>
          ))}
        </div>
      </div>
    </>
  );
}
