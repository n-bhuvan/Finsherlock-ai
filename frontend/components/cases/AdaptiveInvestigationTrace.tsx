"use client";

import { useEffect, useState } from "react";
import {
  Compass,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Shield,
  Coins,
  ArrowRight,
  TrendingDown,
  Info,
  Sliders,
  Layers,
} from "lucide-react";
import { AdaptiveInvestigationResponse, AdaptiveInvestigationStep } from "@/types/investigation";
import { getAdaptiveInvestigationTrace } from "@/lib/api";

interface AdaptiveInvestigationTraceProps {
  transactionId: string;
}

export function AdaptiveInvestigationTrace({ transactionId }: AdaptiveInvestigationTraceProps) {
  const [data, setData] = useState<AdaptiveInvestigationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getAdaptiveInvestigationTrace(transactionId).then((res) => {
      if (!isMounted) return;
      if (res.data) {
        setData(res.data);
      } else {
        setError(res.error || "Failed to load adaptive investigation trace.");
      }
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [transactionId]);

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] text-slate-400 font-mono text-xs flex items-center gap-2 animate-pulse">
        <Compass className="w-4 h-4 text-cyan-400 animate-spin" />
        <span>Executing deterministic uncertainty-driven investigation session...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-slate-800 text-slate-400 font-mono text-xs flex items-center gap-2">
        <Info className="w-4 h-4 text-slate-500 shrink-0" />
        <span>Adaptive Investigation: {error || "Unavailable"}</span>
      </div>
    );
  }

  const budgetPct = Math.min(100, Math.round((data.total_tool_cost / data.max_tool_budget) * 100));
  const relRedPct = Math.round(data.relative_uncertainty_reduction * 100);

  return (
    <div className="rounded-xl bg-[#0b151b] border border-[#142a32] overflow-hidden shadow-xl">
      {/* Header Banner */}
      <div className="p-4 sm:p-5 border-b border-[#142a32] bg-[#071015]/70 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <Compass className="w-5 h-5 text-cyan-400" />
            <h3 className="font-semibold text-white text-base">
              Adaptive Uncertainty-Driven Investigation Trace
            </h3>
            <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-cyan-950 border border-cyan-500/40 text-cyan-300">
              V2 Stage 17
            </span>
            <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-900 border border-slate-700 text-slate-400">
              EIG + Stopping Policy
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Answers &ldquo;What should we investigate next, how much information could it provide, what did we learn, and when should we stop?&rdquo;
          </p>
        </div>

        {/* Uncertainty Transition Callout */}
        <div className="flex items-center gap-4 shrink-0">
          <div className="text-right">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">
              Uncertainty (U₀ → Uₖ)
            </div>
            <div className="flex items-center justify-end gap-1.5 mt-0.5 font-mono">
              <span className="text-sm text-slate-300">
                {(data.initial_uncertainty * 100).toFixed(1)}%
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-base font-bold text-cyan-300">
                {(data.final_uncertainty * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="pl-3 border-l border-[#142a32] text-right">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">
              Reduction
            </div>
            <span
              className={`inline-block px-2.5 py-1 text-xs font-bold font-mono rounded ${
                relRedPct > 0
                  ? "bg-emerald-950/80 border border-emerald-500/50 text-emerald-300"
                  : "bg-slate-900 border border-slate-700 text-slate-400"
              }`}
            >
              {relRedPct > 0 ? `-${relRedPct}%` : "0%"}
            </span>
          </div>
        </div>
      </div>

      {/* Stopping Policy Banner */}
      <div className="p-3.5 px-4 sm:px-5 border-b border-[#142a32] bg-[#071015]/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <div className="text-xs">
            <span className="text-slate-400">Stopping Trigger: </span>
            <span className="font-semibold text-white font-mono">
              {data.stopping_reason.replace(/_/g, " ")}
            </span>
            <span className="text-slate-400 ml-2">— {data.stopping_rationale}</span>
          </div>
        </div>

        {/* Tool Budget Meter */}
        <div className="flex items-center gap-3 shrink-0 text-xs">
          <div className="text-slate-400 text-[11px] font-mono">
            Budget: <span className="text-white font-semibold">₹{data.total_tool_cost.toFixed(2)}</span> / ₹{data.max_tool_budget.toFixed(2)}
          </div>
          <div className="w-20 h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full ${
                budgetPct > 80 ? "bg-amber-400" : "bg-cyan-400"
              }`}
              style={{ width: `${budgetPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Investigation Steps Trace */}
      <div className="p-4 sm:p-5 border-b border-[#142a32]">
        <div className="flex items-center justify-between mb-3">
          <div className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Investigation Step Trace ({data.step_count} of {data.max_steps} steps)</span>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">
            {data.evidence_ids.length} Evidence IDs Discovered
          </span>
        </div>

        {data.steps.length === 0 ? (
          <div className="p-4 rounded-lg bg-[#071015]/60 border border-[#142a32] text-xs text-slate-400 font-mono text-center">
            Zero tool calls executed. Uncertainty was already below stopping threshold (U₀ ≤ 0.12).
          </div>
        ) : (
          <div className="space-y-3">
            {data.steps.map((step) => {
              const isStrong = step.evidence_quality === "STRONG";
              const isConflict = step.evidence_quality === "CONFLICTING";

              return (
                <div
                  key={step.step_number}
                  className="p-3.5 rounded-lg bg-[#071015]/80 border border-[#142a32] flex flex-col gap-2.5 transition-colors hover:border-slate-700"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="w-5 h-5 rounded-full bg-cyan-950 border border-cyan-500/40 text-cyan-300 font-mono text-[10px] flex items-center justify-center font-bold">
                        {step.step_number}
                      </span>
                      <span className="font-mono text-xs font-bold text-white">
                        {step.tool_name}
                      </span>
                      <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-900 border border-slate-700 text-slate-300">
                        ₹{step.tool_cost.toFixed(0)}
                      </span>
                      <span
                        className={`px-2 py-0.5 text-[10px] font-mono rounded border ${
                          isStrong
                            ? "bg-emerald-950/70 border-emerald-500/40 text-emerald-300"
                            : isConflict
                            ? "bg-rose-950/70 border-rose-500/40 text-rose-300"
                            : "bg-slate-900 border-slate-700 text-slate-400"
                        }`}
                      >
                        {step.evidence_quality.replace(/_/g, " ")} ({step.evidence_count} records)
                      </span>
                    </div>

                    <div className="flex items-center gap-3 font-mono text-[11px] shrink-0 text-slate-400">
                      <span>EIG: <strong className="text-cyan-300">{step.estimated_information_gain.toFixed(3)}</strong></span>
                      <span className="text-slate-600">|</span>
                      <span>
                        U: {(step.uncertainty_before * 100).toFixed(1)}% →{" "}
                        <strong className="text-white">{(step.uncertainty_after * 100).toFixed(1)}%</strong>
                      </span>
                    </div>
                  </div>

                  {/* Factual Step Explanation */}
                  <p className="text-xs text-slate-300 leading-relaxed font-sans pl-7">
                    {step.step_rationale}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Cross-Stage Intelligence Integration Grid */}
      <div className="p-4 sm:p-5 grid grid-cols-2 sm:grid-cols-4 gap-3 border-b border-[#142a32] bg-[#071015]/20 font-mono text-xs">
        <div className="p-2.5 rounded bg-[#071015] border border-slate-800">
          <span className="text-[10px] text-slate-400 block uppercase">Calibrated Risk</span>
          <span className="text-sm text-white font-bold">
            {(data.calibrated_risk_score * 100).toFixed(1)}%
          </span>
          <span className="text-[9px] text-slate-400 block mt-0.5">Model B Platt</span>
        </div>

        <div className="p-2.5 rounded bg-[#071015] border border-slate-800">
          <span className="text-[10px] text-slate-400 block uppercase">Stage 15 Anomaly</span>
          <span className="text-sm text-white font-bold">
            {data.stage15_systemic_anomaly_score !== null && data.stage15_systemic_anomaly_score !== undefined
              ? `${(data.stage15_systemic_anomaly_score * 100).toFixed(1)}%`
              : "N/A"}
          </span>
          <span className="text-[9px] text-slate-400 block mt-0.5">Multi-Scope</span>
        </div>

        <div className="p-2.5 rounded bg-[#071015] border border-slate-800">
          <span className="text-[10px] text-slate-400 block uppercase">Stage 16 Priority</span>
          <span className="text-sm text-white font-bold">
            {data.stage16_priority_score !== null && data.stage16_priority_score !== undefined
              ? `${(data.stage16_priority_score * 100).toFixed(1)}%`
              : "N/A"}
          </span>
          <span className="text-[9px] text-slate-400 block mt-0.5">
            {data.stage16_priority_rank ? `Rank #${data.stage16_priority_rank}` : "Queue"}
          </span>
        </div>

        <div className="p-2.5 rounded bg-[#071015] border border-slate-800">
          <span className="text-[10px] text-slate-400 block uppercase">Stage 16 EV</span>
          <span
            className={`text-sm font-bold ${
              (data.stage16_expected_value ?? 0) > 0 ? "text-cyan-300" : "text-amber-400"
            }`}
          >
            {data.stage16_expected_value !== null && data.stage16_expected_value !== undefined
              ? `₹${data.stage16_expected_value.toLocaleString("en-IN", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
              : "N/A"}
          </span>
          <span className="text-[9px] text-slate-400 block mt-0.5">Expected Net Value</span>
        </div>
      </div>

      {/* Safety & Human Approval Safeguard */}
      <div className="p-3.5 bg-[#071015] flex items-start gap-2.5 text-[11px] text-slate-400">
        <Shield className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div className="flex-1">
          <span className="font-semibold text-slate-300">Defense-Only Governance: </span>
          <span>{data.disclaimer} Human review remains mandatory prior to any action.</span>
        </div>
      </div>
    </div>
  );
}
