import { BaselineRiskResponse, NetworkRiskResponse } from "@/types/risk";
import { GitCompare, Network, Activity, HelpCircle } from "lucide-react";
import { formatProbability } from "@/lib/format";

interface RiskComparisonProps {
  baseline: BaselineRiskResponse | null;
  network: NetworkRiskResponse | null;
  loading: boolean;
}

export function RiskComparison({ baseline, network, loading }: RiskComparisonProps) {
  if (loading || !baseline || !network) {
    return (
      <div className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] animate-pulse space-y-3">
        <div className="h-5 bg-[#11242b] rounded w-1/4" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-28 bg-[#11242b] rounded" />
          <div className="h-28 bg-[#11242b] rounded" />
        </div>
      </div>
    );
  }

  const baseProb = formatProbability(baseline.predicted_ring_probability);
  const netProb = formatProbability(network.predicted_ring_probability);

  return (
    <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4 select-none">
      <div className="flex items-center justify-between border-b border-[#142a32] pb-3">
        <div className="flex items-center gap-2">
          <GitCompare className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">
            Model A vs Model B Risk Comparison
          </h2>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#11242b] text-slate-400 border border-[#193843]">
          Dual Model Evaluation
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
        {/* Model A Card */}
        <div className="p-4 rounded-lg bg-[#081216] border border-[#142a32] space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-300 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-slate-400" />
              Model A (Baseline)
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] bg-[#11242b] text-slate-400 border border-[#193843]">
              37 Features
            </span>
          </div>

          <div className="flex items-baseline justify-between pt-1">
            <span className="text-slate-400 text-[11px]">Transaction + Behavioral:</span>
            <span className="text-xl font-extrabold text-slate-200">{baseProb}</span>
          </div>

          <div className="pt-2 border-t border-[#142a32]/80 space-y-1 text-[11px] text-slate-400">
            <div className="flex justify-between">
              <span>Graph Features:</span>
              <span className="text-slate-500">0 (Excluded)</span>
            </div>
            <div className="flex justify-between">
              <span>Risk Band:</span>
              <span className={baseline.risk_band === "HIGH" ? "text-rose-400" : "text-emerald-400"}>
                {baseline.risk_band}
              </span>
            </div>
          </div>
        </div>

        {/* Model B Card */}
        <div className="p-4 rounded-lg bg-[#08161c] border border-cyan-500/30 space-y-3 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-16 h-16 bg-cyan-500/5 rounded-bl-full pointer-events-none" />

          <div className="flex items-center justify-between">
            <span className="font-semibold text-cyan-300 flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-cyan-400" />
              Model B (Graph-Enhanced)
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-950/80 text-cyan-300 border border-cyan-700/50">
              58 Features (+21 Graph)
            </span>
          </div>

          <div className="flex items-baseline justify-between pt-1">
            <span className="text-slate-300 text-[11px]">Network + Topology Context:</span>
            <span className="text-xl font-extrabold text-cyan-300">{netProb}</span>
          </div>

          <div className="pt-2 border-t border-[#142a32]/80 space-y-1 text-[11px] text-slate-400">
            <div className="flex justify-between">
              <span>Graph Features:</span>
              <span className="text-cyan-400 font-semibold">21 (Point-in-Time Safe)</span>
            </div>
            <div className="flex justify-between">
              <span>Risk Band:</span>
              <span className={network.risk_band === "HIGH" ? "text-rose-400" : "text-emerald-400"}>
                {network.risk_band}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Model Ceiling / Delta Truthfulness Notice */}
      <div className="p-3 rounded-lg bg-[#081216]/80 border border-[#142a32] text-[11px] text-slate-400 flex items-start gap-2">
        <HelpCircle className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-slate-300">Technical Context:</strong> Both Model A and Model B evaluate high-risk synthetic ring cases with high confidence (1.0 vs 1.0, Delta: 0.0) due to synthetic feature separability. Model B&apos;s primary operational advantage is providing the 21 structural graph features that enable automated Stage 9 evidence synthesis and Stage 10 investigation tools.
        </p>
      </div>
    </section>
  );
}
