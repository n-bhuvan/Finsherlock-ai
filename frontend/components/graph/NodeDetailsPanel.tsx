import { X, Database } from "lucide-react";
import { GraphNodeData } from "@/types/graph";

interface NodeDetailsPanelProps {
  node: GraphNodeData | null;
  onClose: () => void;
}

export function NodeDetailsPanel({ node, onClose }: NodeDetailsPanelProps) {
  if (!node) return null;

  return (
    <div className="absolute top-4 right-4 z-20 w-80 p-4 rounded-xl bg-[#08151c]/95 border border-cyan-500/40 shadow-2xl backdrop-blur-md text-xs font-mono select-none animate-in fade-in duration-150">
      <div className="flex items-center justify-between border-b border-[#142a32] pb-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400" />
          <span className="font-bold text-white uppercase tracking-wide text-[11px]">
            {node.type} Details
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-[#11242b] text-slate-400 hover:text-white transition cursor-pointer"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="space-y-2.5">
        <div>
          <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Identifier</span>
          <p className="font-bold text-cyan-300 text-sm">{node.id}</p>
        </div>

        {node.sublabel && (
          <div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Context</span>
            <p className="text-slate-200">{node.sublabel}</p>
          </div>
        )}

        {node.metadata && Object.keys(node.metadata).length > 0 && (
          <div className="pt-2 border-t border-[#142a32] space-y-1.5">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">
              Verified Database Attributes
            </span>
            <div className="space-y-1 bg-[#050e12] p-2.5 rounded-lg border border-[#142a32]">
              {Object.entries(node.metadata).map(([k, v]) => (
                <div key={k} className="flex justify-between text-[11px]">
                  <span className="text-slate-400">{k}:</span>
                  <span className="text-slate-200 font-semibold">{String(v)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="pt-2 border-t border-[#142a32] flex items-center gap-1.5 text-[10px] text-slate-500">
          <Database className="w-3 h-3 text-cyan-500" />
          <span>Verified PostgreSQL Entity</span>
        </div>
      </div>
    </div>
  );
}
