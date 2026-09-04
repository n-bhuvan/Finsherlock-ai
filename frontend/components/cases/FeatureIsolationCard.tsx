"use client";

import { useEffect, useState } from "react";
import { Sliders, HelpCircle, ShieldAlert, CheckCircle2, ArrowRight, Activity } from "lucide-react";
import { FeatureIsolationResponse } from "@/types/risk";
import { getTransactionFeatureIsolation } from "@/lib/api";
import { formatProbability } from "@/lib/format";

interface FeatureIsolationCardProps {
  transactionId: string;
}

export function FeatureIsolationCard({ transactionId }: FeatureIsolationCardProps) {
  const [data, setData] = useState<FeatureIsolationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getTransactionFeatureIsolation(transactionId).then((res) => {
      if (!isMounted) return;
      if (res.data) {
        setData(res.data);
      } else {
        setError(res.error || "Failed to load feature isolation analysis.");
      }
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [transactionId]);

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] font-mono text-xs text-slate-400 animate-pulse">
        Evaluating in-silico model feature sensitivity...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-rose-900/30 font-mono text-xs text-rose-400">
        Feature sensitivity analysis unavailable: {error}
      </div>
    );
  }

  const origFormatted = formatProbability(data.original_probability);
  const isoFormatted = formatProbability(data.isolated_probability);
  const deltaSign = data.delta >= 0 ? "+" : "";
  const pctDeltaStr = `${deltaSign}${data.percentage_point_delta.toFixed(2)} pp`;

  return (
    <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4 font-mono text-xs select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#142a32] pb-3">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-cyan-400" />
          <h3 className="font-bold text-white text-sm">
            Model Feature-Isolation Sensitivity Analysis
          </h3>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-950/80 text-cyan-300 border border-cyan-700/50 w-fit">
          In-Silico Ablation: 21 Graph Features Neutralized
        </span>
      </div>

      {/* Probability Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Original */}
        <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32] space-y-1">
          <div className="text-[11px] text-slate-400">Original Model B (58 Feat)</div>
          <div className="text-lg font-bold text-white tracking-wide">{origFormatted}</div>
          <div className="text-[10px] text-cyan-400">Band: {data.risk_band_original}</div>
        </div>

        {/* Isolated */}
        <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32] space-y-1">
          <div className="text-[11px] text-slate-400">Isolated Baseline (37 Feat Preserved)</div>
          <div className="text-lg font-bold text-slate-200 tracking-wide">{isoFormatted}</div>
          <div className="text-[10px] text-slate-400">Band: {data.risk_band_isolated}</div>
        </div>

        {/* Measured Delta */}
        <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32] space-y-1">
          <div className="text-[11px] text-slate-400">Measured Sensitivity Shift (Δ)</div>
          <div className="text-lg font-bold text-cyan-300 tracking-wide">{pctDeltaStr}</div>
          <div className="text-[10px] text-slate-400">
            Raw Δ: {data.delta >= 0 ? "+" : ""}{data.delta.toFixed(6)}
          </div>
        </div>
      </div>

      {/* Visual Bars */}
      <div className="space-y-2 p-3 rounded-lg bg-[#081216] border border-[#142a32]/60 text-[11px]">
        <div>
          <div className="flex justify-between text-slate-400 mb-1">
            <span>Model B Original Score</span>
            <span className="font-semibold text-white">{origFormatted}</span>
          </div>
          <div className="h-2 w-full bg-[#050b0e] rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                data.risk_band_original === "HIGH"
                  ? "bg-rose-500"
                  : data.risk_band_original === "MEDIUM"
                  ? "bg-amber-500"
                  : "bg-emerald-500"
              }`}
              style={{ width: `${Math.min(100, Math.max(0, data.original_probability * 100))}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-slate-400 mb-1">
            <span>Isolated-Entity Baseline Vector</span>
            <span className="font-semibold text-slate-300">{isoFormatted}</span>
          </div>
          <div className="h-2 w-full bg-[#050b0e] rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                data.risk_band_isolated === "HIGH"
                  ? "bg-rose-500"
                  : data.risk_band_isolated === "MEDIUM"
                  ? "bg-amber-500"
                  : "bg-emerald-500"
              }`}
              style={{ width: `${Math.min(100, Math.max(0, data.isolated_probability * 100))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Provenance-Grounded Evidence Mapping */}
      <div className="space-y-2">
        <div className="text-[11px] font-bold text-slate-300 flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span>Provenance-Grounded Evidence Mapping (Top Model B Graph Features)</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-[11px]">
            <thead>
              <tr className="border-b border-[#142a32] text-slate-400">
                <th className="py-1.5 px-2">Feature Name</th>
                <th className="py-1.5 px-2">Model B Rank</th>
                <th className="py-1.5 px-2">Observed</th>
                <th className="py-1.5 px-2">Isolated Base</th>
                <th className="py-1.5 px-2">Stage 9 Corroborating Evidence</th>
                <th className="py-1.5 px-2">Provenance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#142a32]/60 text-slate-300">
              {data.attributions.slice(0, 5).map((attr) => (
                <tr key={attr.feature_name} className="hover:bg-[#081216]">
                  <td className="py-1.5 px-2 font-mono text-cyan-300">{attr.feature_name}</td>
                  <td className="py-1.5 px-2 text-slate-400">#{attr.importance_rank_in_model_b}</td>
                  <td className="py-1.5 px-2 font-semibold text-white">{attr.original_value}</td>
                  <td className="py-1.5 px-2 text-slate-400">{attr.isolated_value}</td>
                  <td className="py-1.5 px-2">
                    {attr.corroborating_evidence_id ? (
                      <span className="text-cyan-400 underline font-mono text-[10px]">
                        {attr.corroborating_evidence_id}
                      </span>
                    ) : (
                      <span className="text-slate-500 text-[10px]">No direct signal</span>
                    )}
                  </td>
                  <td className="py-1.5 px-2">
                    {attr.provenance_status === "VERIFIED" ? (
                      <span className="text-emerald-400 text-[10px] inline-flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> VERIFIED
                      </span>
                    ) : (
                      <span className="text-slate-500 text-[10px]">FEATURE_ONLY</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Scientific Honesty & Limitations Banner */}
      <div className="p-3 rounded-lg bg-[#08161d] border border-cyan-800/40 space-y-1 text-[11px] leading-relaxed">
        <div className="flex items-center gap-1.5 font-bold text-cyan-300">
          <HelpCircle className="w-3.5 h-3.5" />
          <span>Scientific Methodology &amp; Boundaries</span>
        </div>
        <p className="text-slate-300 font-sans">{data.methodology}</p>
        <ul className="list-disc list-inside space-y-0.5 text-slate-400 font-sans text-[10.5px] pt-1">
          {data.limitations.map((lim, idx) => (
            <li key={idx}>{lim}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
