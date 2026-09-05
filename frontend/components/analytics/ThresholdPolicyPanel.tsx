"use client";

import { useState, useEffect } from "react";
import {
  Sliders,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ShieldCheck,
  DollarSign,
  AlertCircle,
  HelpCircle,
} from "lucide-react";
import { ThresholdOptimizationResponse } from "@/types/analytics";

export function ThresholdPolicyPanel() {
  const [data, setData] = useState<ThresholdOptimizationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [sensitivityScope, setSensitivityScope] = useState<"held_out" | "val">("held_out");

  useEffect(() => {
    async function fetchThresholdData() {
      try {
        const res = await fetch("http://localhost:8000/api/analytics/threshold-policies");
        if (res.ok) {
          const json = await res.json();
          setData(json);
        } else {
          setData({ status: "Unavailable", message: "API returned non-200 status" });
        }
      } catch (err) {
        setData({ status: "Unavailable", message: "Backend offline or unreachable" });
      } finally {
        setLoading(false);
      }
    }
    fetchThresholdData();
  }, []);

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] text-slate-400 font-mono text-xs flex items-center gap-2">
        <div className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        Loading Operational Threshold Optimization...
      </div>
    );
  }

  if (!data || data.status === "Unavailable" || !data.validation_derived_policies) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] text-slate-400 font-mono text-xs space-y-2">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <AlertTriangle className="w-4 h-4" />
          <span>Threshold Optimization Benchmark Unavailable</span>
        </div>
        <p className="text-[11px] text-slate-500">
          Threshold policy artifacts not loaded. Run <code className="text-cyan-300">python scripts/run_stage14_evaluation.py</code> to generate benchmark data.
        </p>
      </div>
    );
  }

  const policies = data.validation_derived_policies;
  const testResults = data.held_out_test_evaluation || {};
  const sensitivity =
    sensitivityScope === "held_out" && data.held_out_test_sensitivity_analysis
      ? data.held_out_test_sensitivity_analysis
      : data.economic_sensitivity_analysis || [];

  return (
    <div className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-[#142a32] pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white font-sans tracking-wide">
              Threshold Policy Optimization &amp; Economic Sensitivity (Stage 14)
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950/80 border border-cyan-700/60 text-cyan-300">
              4 Frozen Policies
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans">
            Optimized on Val-Thresh (N=150) and frozen before evaluation on the held-out test set (N=300). Evaluates economic sensitivity across 4 interception tiers.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1 rounded bg-[#081216] border border-cyan-500/30 text-[10px] text-cyan-300">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>Recommended Policy: T*_Economic</span>
        </div>
      </div>

      {/* 4 Discrete Policy Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {Object.entries(policies).map(([key, policy]) => {
          const testEval = testResults[key];
          const isRecommended = policy.is_recommended;
          const isFeasible = policy.status === "FEASIBLE";

          return (
            <div
              key={key}
              className={`p-3.5 rounded-xl border transition-all flex flex-col justify-between ${
                isRecommended
                  ? "bg-[#081820] border-cyan-500/60 shadow-lg shadow-cyan-950/20 ring-1 ring-cyan-500/30"
                  : "bg-[#081216] border-[#142a32]"
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    {key}
                  </span>
                  {isRecommended ? (
                    <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 uppercase">
                      RECOMMENDED
                    </span>
                  ) : isFeasible ? (
                    <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-700/60 uppercase">
                      FEASIBLE
                    </span>
                  ) : (
                    <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-rose-950 text-rose-300 border border-rose-700/60 uppercase">
                      INFEASIBLE
                    </span>
                  )}
                </div>

                <div className="font-bold text-white font-sans text-xs leading-tight">
                  {policy.scenario_name}
                </div>

                <p className="text-[10px] text-slate-400 font-sans line-clamp-2">
                  {policy.description}
                </p>

                <div className="pt-2 border-t border-[#142a32]/60 space-y-1">
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-slate-400">Frozen Threshold:</span>
                    <span className="font-bold text-cyan-300 font-mono">
                      {policy.threshold !== null ? `T = ${policy.threshold.toFixed(2)}` : "None"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-slate-400">Val {policy.primary_metric}:</span>
                    <span className="font-mono text-slate-200">
                      {policy.primary_metric === "modeled_net_value_saved"
                        ? `Rs. ${policy.primary_value.toLocaleString()}`
                        : policy.primary_value.toFixed(4)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Test Evaluation Metric at Frozen Threshold */}
              <div className="mt-3 pt-2 border-t border-[#142a32] space-y-1">
                <span className="text-[9px] text-slate-500 uppercase tracking-wider block">
                  Held-Out Test Generalization:
                </span>
                {testEval && testEval.metrics ? (
                  <div className="space-y-1 text-[10px] font-mono">
                    <div className="grid grid-cols-2 gap-1">
                      <div className="bg-[#0b151b] p-1 rounded text-center">
                        <span className="text-slate-400 text-[9px] block">F1 Score</span>
                        <span className="text-cyan-300 font-bold">{testEval.metrics.f1.toFixed(4)}</span>
                      </div>
                      <div className="bg-[#0b151b] p-1 rounded text-center">
                        <span className="text-slate-400 text-[9px] block">Recall</span>
                        <span className="text-emerald-300 font-bold">{testEval.metrics.recall.toFixed(4)}</span>
                      </div>
                    </div>
                    {testEval.modeled_economics && (
                      <div className="bg-[#0b151b] p-1.5 rounded text-left space-y-0.5 border border-[#142a32]">
                        <div className="flex justify-between text-[9px] text-slate-400">
                          <span>Loss Avoided (85%):</span>
                          <span className="text-slate-200">Rs. {testEval.modeled_economics.modeled_loss_avoided.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-[9px] text-slate-400">
                          <span>FP Friction ({testEval.modeled_economics.fp_count ?? 0} &times; Rs.1.2k):</span>
                          <span className="text-slate-400">- Rs. {testEval.modeled_economics.modeled_friction_cost.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-[9px] text-slate-400">
                          <span>Review Cost ({testEval.modeled_economics.flagged_case_count ?? 26} &times; Rs.350):</span>
                          <span className="text-slate-400">- Rs. {testEval.modeled_economics.modeled_investigation_cost.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-[10px] font-bold text-cyan-300 pt-0.5 border-t border-[#142a32]">
                          <span>Net Value Saved:</span>
                          <span>Rs. {testEval.modeled_economics.modeled_net_value_saved.toLocaleString()}</span>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-[10px] text-amber-400/80 italic">
                    {testEval?.status ?? "Not Evaluated"}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Economic Sensitivity Analysis Table */}
      <div className="space-y-2 pt-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <DollarSign className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-xs font-bold text-white font-sans">
              Economic Sensitivity Analysis Across Interception Tiers (50% – 100%)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 bg-[#081216] p-0.5 rounded border border-[#142a32]">
              <button
                onClick={() => setSensitivityScope("held_out")}
                className={`px-2 py-0.5 rounded text-[10px] transition-all ${
                  sensitivityScope === "held_out"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Held-Out Test (N=300)
              </button>
              <button
                onClick={() => setSensitivityScope("val")}
                className={`px-2 py-0.5 rounded text-[10px] transition-all ${
                  sensitivityScope === "val"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Val-Thresh (N=150)
              </button>
            </div>
            <span className="text-[10px] text-slate-500 hidden md:inline">
              CFP = Rs. 1,200 | Cinv = Rs. 350
            </span>
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-[#142a32]">
          <table className="w-full text-left bg-[#081216]">
            <thead>
              <tr className="text-[10px] text-slate-400 border-b border-[#142a32] bg-[#0b151b]">
                <th className="py-2 px-2">Interception Tier</th>
                <th className="py-2 px-2 text-center">Threshold</th>
                <th className="py-2 px-2 text-right">Flagged (TP+FP)</th>
                <th className="py-2 px-2 text-right">Modeled Loss Avoided</th>
                <th className="py-2 px-2 text-right">Friction (FP)</th>
                <th className="py-2 px-2 text-right">Review (Cases)</th>
                <th className="py-2 px-2 text-right">Modeled Net Saved</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#142a32]/60 text-[11px]">
              {sensitivity.map((tier: any, idx: number) => {
                const isDefault = tier.interception_rate === 0.85;
                const appliedThreshold = tier.threshold_applied ?? tier.optimal_threshold;
                const caseCount = tier.flagged_case_count ?? (tier.tp_count !== undefined ? tier.tp_count + (tier.fp_count ?? 0) : "-");
                return (
                  <tr
                    key={idx}
                    className={`hover:bg-[#0b151b]/60 ${
                      isDefault ? "bg-cyan-950/20 text-cyan-200 font-semibold" : "text-slate-300"
                    }`}
                  >
                    <td className="py-2 px-2">
                      <div className="flex items-center gap-1.5">
                        <span>{tier.interception_tier_label}</span>
                        {isDefault && (
                          <span className="px-1 py-0.2 rounded text-[8px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 uppercase">
                            DEFAULT
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2 px-2 text-center font-mono text-cyan-300">
                      T = {typeof appliedThreshold === "number" ? appliedThreshold.toFixed(2) : appliedThreshold}
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-slate-300">
                      {caseCount}
                    </td>
                    <td className="py-2 px-2 text-right font-mono">
                      Rs. {tier.modeled_loss_avoided.toLocaleString()}
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-slate-400">
                      Rs. {tier.modeled_friction_cost.toLocaleString()}
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-slate-400">
                      Rs. {tier.modeled_investigation_cost.toLocaleString()}
                    </td>
                    <td className="py-2 px-2 text-right font-mono font-bold text-cyan-300">
                      Rs. {tier.modeled_net_value_saved.toLocaleString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mandatory Financial Disclaimers */}
      <div className="p-3.5 rounded-lg bg-[#08161d] border border-cyan-500/20 text-[10px] text-slate-400 font-sans space-y-1">
        <div className="flex items-center gap-1.5 font-bold text-cyan-300">
          <AlertCircle className="w-3.5 h-3.5" />
          <span>Operational Modeling &amp; Economic Disclosure</span>
        </div>
        <p className="leading-relaxed">
          {data.metadata?.modeling_assumptions?.disclosure ??
            "Financial figures represent modeled loss avoided and modeled net value saved under stated operational assumptions."}
          {" "}Exposure calculations use: Modeled Net Value Saved = Modeled Loss Avoided (Exposure × Interception Rate) − False Positive Friction Cost (Rs. 1,200/FP) − Investigation Cost (Rs. 350/case).
        </p>
      </div>
    </div>
  );
}
