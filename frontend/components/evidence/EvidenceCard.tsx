import { EvidenceItem } from "@/types/evidence";
import {
  ShieldAlert,
  Smartphone,
  Wifi,
  Users,
  GitFork,
  Clock,
  Database,
  Tag,
} from "lucide-react";

interface EvidenceCardProps {
  item: EvidenceItem;
}

function getEvidenceIcon(type: string) {
  switch (type) {
    case "SHARED_DEVICE":
      return <Smartphone className="w-4 h-4 text-emerald-400" />;
    case "SHARED_IP":
      return <Wifi className="w-4 h-4 text-amber-400" />;
    case "COMMON_BENEFICIARY":
    case "RELATED_ACCOUNT":
      return <Users className="w-4 h-4 text-cyan-400" />;
    case "RAPID_FUND_FLOW":
    case "MULTI_HOP_CONNECTION":
      return <GitFork className="w-4 h-4 text-rose-400" />;
    default:
      return <ShieldAlert className="w-4 h-4 text-slate-400" />;
  }
}

export function EvidenceCard({ item }: EvidenceCardProps) {
  const isHigh = item.severity === "HIGH";
  const isMedium = item.severity === "MEDIUM";

  return (
    <div className="p-4 rounded-lg bg-[#081216] border border-[#142a32] hover:border-cyan-500/40 transition space-y-3 font-mono text-xs">
      {/* Card Header: Rank, Severity, Type */}
      <div className="flex items-center justify-between gap-2 border-b border-[#142a32]/80 pb-2">
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded-full bg-[#11242b] border border-[#1a3843] flex items-center justify-center text-[10px] font-bold text-cyan-300">
            #{item.rank}
          </span>
          <div className="flex items-center gap-1.5 font-sans font-semibold text-white">
            {getEvidenceIcon(item.evidence_type)}
            <span className="truncate">{item.title}</span>
          </div>
        </div>

        <span
          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
            isHigh
              ? "bg-rose-950/70 border-rose-700/60 text-rose-300"
              : isMedium
              ? "bg-amber-950/70 border-amber-700/60 text-amber-300"
              : "bg-cyan-950/70 border-cyan-700/60 text-cyan-300"
          }`}
        >
          {item.severity}
        </span>
      </div>

      {/* Description */}
      <p className="text-slate-300 font-sans text-xs leading-relaxed">
        {item.description}
      </p>

      {/* Supporting Record IDs and Entities */}
      {(item.supporting_transaction_ids.length > 0 || item.related_entities.length > 0) && (
        <div className="pt-2 border-t border-[#142a32]/60 space-y-1 text-[11px]">
          {item.supporting_transaction_ids.length > 0 && (
            <div className="flex items-center gap-1.5 text-slate-400 overflow-x-auto py-0.5">
              <span className="text-slate-500 text-[10px] flex-shrink-0">Txs:</span>
              {item.supporting_transaction_ids.slice(0, 3).map((txId) => (
                <span key={txId} className="px-1.5 py-0.5 rounded bg-[#0b161b] border border-[#142a32] text-slate-300 text-[10px]">
                  {txId}
                </span>
              ))}
              {item.supporting_transaction_ids.length > 3 && (
                <span className="text-slate-500 text-[10px]">+{item.supporting_transaction_ids.length - 3}</span>
              )}
            </div>
          )}

          {item.related_entities.length > 0 && (
            <div className="flex items-center gap-1.5 text-slate-400 overflow-x-auto py-0.5">
              <span className="text-slate-500 text-[10px] flex-shrink-0">Entities:</span>
              {item.related_entities.slice(0, 3).map((entId) => (
                <span key={entId} className="px-1.5 py-0.5 rounded bg-[#0b161b] border border-[#142a32] text-cyan-400 text-[10px]">
                  {entId}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Footer: Provenance & Evidence ID */}
      <div className="pt-2 border-t border-[#142a32]/60 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-500">
        <div className="flex items-center gap-1">
          <Database className="w-3 h-3 text-cyan-500" />
          <span title={item.timestamp_source}>{item.source}</span>
        </div>

        <div className="flex items-center gap-1" title={item.evidence_id}>
          <Tag className="w-3 h-3 text-slate-500" />
          <span className="truncate max-w-[140px] text-slate-400">{item.evidence_id}</span>
        </div>
      </div>
    </div>
  );
}
