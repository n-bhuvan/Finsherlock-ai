import { EvidenceListResponse } from "@/types/evidence";
import { EvidenceCard } from "./EvidenceCard";
import { ShieldCheck, FileText, AlertCircle } from "lucide-react";

interface EvidenceListProps {
  evidence: EvidenceListResponse | null;
  loading: boolean;
  error: string | null;
}

export function EvidenceList({ evidence, loading, error }: EvidenceListProps) {
  if (loading) {
    return (
      <div className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] animate-pulse space-y-4">
        <div className="h-5 bg-[#11242b] rounded w-1/3" />
        <div className="space-y-3">
          <div className="h-24 bg-[#11242b] rounded" />
          <div className="h-24 bg-[#11242b] rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-5 rounded-xl bg-[#0b151b] border border-rose-900/40 text-xs font-mono text-rose-300 space-y-2">
        <div className="flex items-center gap-2 font-bold">
          <AlertCircle className="w-4 h-4 text-rose-400" />
          Unable to load evidence
        </div>
        <p className="text-slate-400">{error}</p>
      </div>
    );
  }

  const items = evidence?.items || [];

  return (
    <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4 select-none">
      <div className="flex items-center justify-between border-b border-[#142a32] pb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">
            Top Evidence &amp; Observations
          </h2>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#11242b] text-cyan-300 border border-[#193843]">
          {items.length} Verified Items
        </span>
      </div>

      {items.length === 0 ? (
        <div className="p-6 rounded-lg bg-[#081216] border border-[#142a32] text-center text-xs font-mono text-slate-400 space-y-2">
          <ShieldCheck className="w-6 h-6 text-emerald-400 mx-auto" />
          <p className="text-slate-300 font-semibold">No Suspicious Evidence Observed</p>
          <p className="text-[11px] text-slate-500">
            This account demonstrates clean transactional behavior with no anomalous shared infrastructure.
          </p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
          {items.map((item) => (
            <EvidenceCard key={item.evidence_id} item={item} />
          ))}
        </div>
      )}

      {evidence?.disclaimer && (
        <p className="text-[10px] text-slate-500 font-mono leading-relaxed border-t border-[#142a32]/60 pt-2">
          {evidence.disclaimer}
        </p>
      )}
    </section>
  );
}
