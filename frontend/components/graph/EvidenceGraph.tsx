"use client";

import { useMemo, useState } from "react";
import {
  ReactFlow,
  Controls,
  Background,
  BackgroundVariant,
  Node,
  Edge,
  MarkerType,
} from "@xyflow/react";
import { EntityNode } from "./CustomNodes";
import { NodeDetailsPanel } from "./NodeDetailsPanel";
import { GraphNodeData } from "@/types/graph";
import { Share2, Maximize2 } from "lucide-react";

interface EvidenceGraphProps {
  nodes: Node<GraphNodeData>[];
  edges: Edge[];
  loading?: boolean;
}

const nodeTypes = {
  entityNode: EntityNode,
};

export function EvidenceGraph({ nodes, edges, loading }: EvidenceGraphProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);

  const styledEdges = useMemo(() => {
    return edges.map((e) => ({
      ...e,
      style: { stroke: "#0d9488", strokeWidth: 1.5, ...e.style },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "#0d9488",
        width: 12,
        height: 12,
      },
    }));
  }, [edges]);

  if (loading) {
    return (
      <div className="h-[460px] w-full rounded-xl bg-[#080f14] border border-[#142a32] flex items-center justify-center font-mono text-xs text-cyan-400 animate-pulse">
        Assembling Verified Entity Graph...
      </div>
    );
  }

  return (
    <div className="relative h-[460px] w-full rounded-xl bg-[#080f14] border border-[#142a32] overflow-hidden shadow-2xl">
      {/* Top Overlay: Title & Legend */}
      <div className="absolute top-3 left-4 z-10 flex flex-wrap items-center gap-3 text-xs font-mono select-none">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0b161b]/90 border border-[#142a32] backdrop-blur-md">
          <Share2 className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-bold text-white text-[11px]">Entity Network Topology</span>
          <span className="text-[10px] text-slate-400">({nodes.length} nodes, {edges.length} edges)</span>
        </div>

        {/* Legend */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-lg bg-[#0b161b]/80 border border-[#142a32] text-[10px] text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400" /> Account
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400" /> Device
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-400" /> IP
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-purple-400" /> Beneficiary
          </span>
        </div>
      </div>

      {/* Inspector Panel */}
      <NodeDetailsPanel
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
      />

      {/* React Flow Canvas */}
      <ReactFlow
        nodes={nodes}
        edges={styledEdges}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => setSelectedNode(node.data)}
        onPaneClick={() => setSelectedNode(null)}
        fitView
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={18}
          size={1}
          color="#163842"
        />
        <Controls showInteractive={false} className="!left-4 !bottom-4" />
      </ReactFlow>
    </div>
  );
}
