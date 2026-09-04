import { ToolExecutionResult } from "@/types/investigation";
import { CheckCircle2, AlertTriangle, Database, ShieldAlert, Tag, Clock } from "lucide-react";

interface ToolResultCardProps {
  result: ToolExecutionResult | null;
  loading: boolean;
  onClose?: () => void;
}

export function ToolResultCard({ result, loading, onClose }: ToolResultCardProps) {
  if (loading) {
    return (
      <div className="p-4 rounded-lg bg-[#081216] border border-[#142a32] animate-pulse space-y-2 text-xs font-mono text-cyan-400">
        Executing controlled investigation tool...
      </div>
    );
  }

  if (!result) return null;

  const isSuccess = result.status === "SUCCESS" || result.status === "LIMITED";

  return (
    <div className="p-4 rounded-xl bg-[#08151c] border border-cyan-500/40 shadow-xl space-y-3 font-mono text-xs select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#142a32] pb-2.5">
        <div className="flex items-center gap-2">
          {isSuccess ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          )}
          <span className="font-bold text-white uppercase tracking-wide">
            Tool: {result.tool_name}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
              result.status === "SUCCESS"
                ? "bg-emerald-950/70 border-emerald-700/60 text-emerald-300"
                : result.status === "LIMITED"
                ? "bg-amber-950/70 border-amber-700/60 text-amber-300"
                : "bg-slate-900 border-slate-700 text-slate-400"
            }`}
          >
            {result.status} ({result.result_count} items)
          </span>
          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-500 hover:text-white transition cursor-pointer text-xs"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Target & Source */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
        <div>
          <span>Target: </span>
          <span className="text-cyan-300 font-semibold">{result.target}</span>
        </div>
        <div className="flex items-center gap-1">
          <Database className="w-3 h-3 text-cyan-500" />
          <span>{result.source}</span>
        </div>
      </div>

      {/* Structured Payload Render */}
      <div className="bg-[#050e12] p-3 rounded-lg border border-[#142a32] max-h-56 overflow-y-auto space-y-1.5 text-[11px]">
        {Array.isArray(result.result) ? (
          result.result.length === 0 ? (
            <p className="text-slate-500 text-center py-2">No matching records found.</p>
          ) : (
            result.result.map((item, idx) => (
              <div
                key={idx}
                className="p-2 rounded bg-[#081216] border border-[#142a32]/60 space-y-0.5"
              >
                {Object.entries(item).map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span className="text-slate-500">{k}:</span>
                    <span className="text-slate-300 truncate max-w-[200px]">
                      {typeof v === "object" ? JSON.stringify(v) : String(v)}
                    </span>
                  </div>
                ))}
              </div>
            ))
          )
        ) : typeof result.result === "object" && result.result !== null ? (
          <div className="space-y-1">
            {Object.entries(result.result).map(([k, v]) => (
              <div key={k} className="flex justify-between border-b border-[#142a32]/40 pb-0.5">
                <span className="text-slate-500">{k}:</span>
                <span className="text-slate-300 truncate max-w-[240px]">
                  {typeof v === "object" ? JSON.stringify(v) : String(v)}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <pre className="text-slate-300 whitespace-pre-wrap">{String(result.result)}</pre>
        )}
      </div>

      {/* Evidence IDs Linked */}
      {result.evidence_ids.length > 0 && (
        <div className="pt-2 border-t border-[#142a32]/60 flex items-center gap-1.5 text-[10px] text-cyan-400">
          <Tag className="w-3 h-3 flex-shrink-0" />
          <span>Stage 9 Evidence: {result.evidence_ids.join(", ")}</span>
        </div>
      )}

      {/* Limitations and Boundary Notice */}
      <div className="pt-2 border-t border-[#142a32]/60 text-[10px] text-slate-500 space-y-0.5">
        {result.limitations && <p>Bound: {result.limitations}</p>}
        <p className="italic">{result.disclaimer}</p>
      </div>
    </div>
  );
}
