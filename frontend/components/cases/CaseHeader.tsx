import { ShieldAlert, AlertTriangle, CheckCircle, Calendar, Hash, ArrowRightLeft, Radio } from "lucide-react";
import { RiskResponse } from "@/types/risk";
import { TransactionRecord } from "@/types/investigation";
import { formatProbability } from "@/lib/format";

interface CaseHeaderProps {
  transaction: TransactionRecord | null;
  risk: RiskResponse | null;
  loading: boolean;
}

export function CaseHeader({ transaction, risk, loading }: CaseHeaderProps) {
  if (loading || !transaction) {
    return (
      <div className="p-6 rounded-xl bg-[#0b151b] border border-[#142a32] animate-pulse space-y-4">
        <div className="h-6 bg-[#11242b] rounded w-1/3" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="h-12 bg-[#11242b] rounded" />
          <div className="h-12 bg-[#11242b] rounded" />
          <div className="h-12 bg-[#11242b] rounded" />
          <div className="h-12 bg-[#11242b] rounded" />
        </div>
      </div>
    );
  }

  const isHighRisk = risk?.risk_band === "HIGH";
  const probFormatted = formatProbability(risk?.predicted_ring_probability);

  return (
    <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4 select-none">
      {/* Top Banner: IDs & Status Badges */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#142a32] pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950/70 border border-cyan-500/30 text-cyan-300 font-semibold">
              CASE INVESTIGATION
            </span>
            <h1 className="text-xl font-bold tracking-tight text-white font-mono flex items-center gap-2">
              {transaction.transaction_id}
            </h1>
          </div>
          <p className="text-xs text-slate-400 font-mono flex items-center gap-2">
            <span>Target Account:</span>
            <span className="text-slate-200 font-semibold">{transaction.account_id}</span>
          </p>
        </div>

        {/* Risk Probability Callout */}
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
              Model Ring Probability
            </p>
            <div className="flex items-baseline justify-end gap-1 font-mono">
              <span
                className={`text-2xl font-extrabold ${
                  isHighRisk ? "text-rose-400" : "text-emerald-400"
                }`}
              >
                {probFormatted}
              </span>
              <span className="text-[11px] text-slate-500">
                (threshold {risk?.decision_threshold || 0.5})
              </span>
            </div>
          </div>

          <div
            className={`px-3.5 py-2 rounded-lg border flex items-center gap-2 ${
              isHighRisk
                ? "bg-rose-950/50 border-rose-600/40 text-rose-300"
                : "bg-emerald-950/50 border-emerald-600/40 text-emerald-300"
            }`}
          >
            {isHighRisk ? (
              <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            ) : (
              <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            )}
            <div className="leading-tight">
              <span className="text-xs font-bold font-mono tracking-wide block">
                {risk?.risk_band || "LOW"} RISK
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                {isHighRisk ? "Investigation Required" : "Standard Profile"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
        <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32]/80 space-y-1">
          <span className="text-slate-500 text-[10px] uppercase tracking-wider flex items-center gap-1">
            <Hash className="w-3 h-3 text-cyan-400" /> Amount (Synthetic)
          </span>
          <p className="text-base font-bold text-white">
            ₹{transaction.amount.toLocaleString("en-IN")}
          </p>
        </div>

        <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32]/80 space-y-1">
          <span className="text-slate-500 text-[10px] uppercase tracking-wider flex items-center gap-1">
            <Calendar className="w-3 h-3 text-cyan-400" /> Timestamp
          </span>
          <p className="text-slate-200 truncate" title={transaction.timestamp}>
            {transaction.timestamp.replace("T", " ").slice(0, 19)}
          </p>
        </div>

        <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32]/80 space-y-1">
          <span className="text-slate-500 text-[10px] uppercase tracking-wider flex items-center gap-1">
            <ArrowRightLeft className="w-3 h-3 text-cyan-400" /> Channel &amp; Type
          </span>
          <p className="text-slate-200">
            {transaction.channel} • {transaction.transaction_type}
          </p>
        </div>

        <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32]/80 space-y-1">
          <span className="text-slate-500 text-[10px] uppercase tracking-wider flex items-center gap-1">
            <Radio className="w-3 h-3 text-cyan-400" /> Transaction Status
          </span>
          <p className="text-emerald-400 font-semibold">{transaction.status}</p>
        </div>
      </div>

      {/* Analytical Notice */}
      <div className="text-[11px] text-slate-400 bg-[#081216]/60 border border-[#142a32]/60 px-3 py-1.5 rounded-md flex items-center gap-2">
        <ShieldAlert className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
        <span>
          Analytical risk assessment output only. Statistical model score does not imply certainty, confirmed fraud, or an automated account action.
        </span>
      </div>
    </section>
  );
}
