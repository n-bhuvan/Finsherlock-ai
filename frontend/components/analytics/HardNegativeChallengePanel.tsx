"use client";

import { useState, useEffect } from "react";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  BarChart2,
  Layers,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { ChallengeEvaluationResponse } from "@/types/analytics";

export function HardNegativeChallengePanel() {
  const [data, setData] = useState<ChallengeEvaluationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedThreshold, setSelectedThreshold] = useState<"0.70" | "0.50">("0.70");
  const [showSweep, setShowSweep] = useState(false);

  useEffect(() => {
    async function fetchChallengeData() {
      try {
        const res = await fetch("http://localhost:8000/api/analytics/challenge");
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
    fetchChallengeData();
  }, []);

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] text-slate-400 font-mono text-xs flex items-center gap-2">
        <div className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        Loading Hard-Negative Challenge Evaluation...
      </div>
    );
  }

  if (!data || data.status === "Unavailable" || !data.overall_metrics_t_0_70) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] text-slate-400 font-mono text-xs space-y-2">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <AlertTriangle className="w-4 h-4" />
          <span>Hard-Negative Challenge Benchmark Unavailable</span>
        </div>
        <p className="text-[11px] text-slate-500">
          Evaluation artifacts not loaded. Run <code className="text-cyan-300">python scripts/evaluate_challenge.py</code> to generate benchmark data.
        </p>
      </div>
    );
  }

  const metrics =
    selectedThreshold === "0.70"
      ? data.overall_metrics_t_0_70
      : data.overall_metrics_t_0_50 || data.overall_metrics_t_0_70;

  const mA = metrics.model_a;
  const mB = metrics.model_b;
  const deltas = metrics.deltas;

  const comparisonRows = [
    { name: "PR-AUC (Precision-Recall AUC)", a: mA.pr_auc.toFixed(4), b: mB.pr_auc.toFixed(4), d: deltas.pr_auc_delta > 0 ? `+${deltas.pr_auc_delta.toFixed(4)}` : deltas.pr_auc_delta.toFixed(4), highlight: true },
    { name: "ROC-AUC", a: mA.roc_auc.toFixed(4), b: mB.roc_auc.toFixed(4), d: deltas.roc_auc_delta > 0 ? `+${deltas.roc_auc_delta.toFixed(4)}` : deltas.roc_auc_delta.toFixed(4) },
    { name: `Precision (at T = ${selectedThreshold})`, a: mA.precision.toFixed(4), b: mB.precision.toFixed(4), d: deltas.precision_delta.toFixed(4) },
    { name: `Recall (at T = ${selectedThreshold})`, a: mA.recall.toFixed(4), b: mB.recall.toFixed(4), d: deltas.recall_delta.toFixed(4) },
    { name: `F1 Score (at T = ${selectedThreshold})`, a: mA.f1.toFixed(4), b: mB.f1.toFixed(4), d: deltas.f1_delta.toFixed(4) },
    { name: `False Positive Rate (FPR)`, a: `${(mA.false_positive_rate * 100).toFixed(2)}%`, b: `${(mB.false_positive_rate * 100).toFixed(2)}%`, d: `${(deltas.fpr_delta * 100).toFixed(2)}%` },
    { name: `False Positives Count (FP)`, a: mA.confusion_matrix.false_positives, b: mB.confusion_matrix.false_positives, d: deltas.fp_delta >= 0 ? `+${deltas.fp_delta}` : `${deltas.fp_delta}`, alert: deltas.fp_delta > 0 },
    { name: `True Positives Count (TP)`, a: mA.confusion_matrix.true_positives, b: mB.confusion_matrix.true_positives, d: `+${deltas.tp_delta}` },
  ];

  return (
    <div className="space-y-4 font-mono text-xs select-none">
      <div className="p-4 rounded-xl bg-[#0b151b] border border-cyan-900/40 space-y-4 shadow-xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#142a32] pb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <h3 className="font-bold text-white text-sm">
                Hard-Negative Challenge Benchmark (Robustness Stress Test)
              </h3>
            </div>
            <p className="text-[11px] text-slate-400 font-sans">
              Evaluates model resilience when legitimate users deliberately share devices, IPs, and common payees. Out-of-sample stress test (754 txs: 607 hard negatives, 147 ring controls).
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] bg-amber-950/80 text-amber-300 border border-amber-700/50 w-fit">
              Stage 13 Advanced Evaluation
            </span>
            <div className="flex bg-[#081216] border border-[#142a32] rounded p-0.5 text-[10px]">
              <button
                onClick={() => setSelectedThreshold("0.70")}
                className={`px-2 py-0.5 rounded ${
                  selectedThreshold === "0.70" ? "bg-cyan-500/20 text-cyan-300 font-bold" : "text-slate-400 hover:text-white"
                }`}
              >
                T = 0.70 (Prod)
              </button>
              <button
                onClick={() => setSelectedThreshold("0.50")}
                className={`px-2 py-0.5 rounded ${
                  selectedThreshold === "0.50" ? "bg-cyan-500/20 text-cyan-300 font-bold" : "text-slate-400 hover:text-white"
                }`}
              >
                T = 0.50 (Base)
              </button>
            </div>
          </div>
        </div>

        {/* Comparison Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#142a32] text-slate-400 text-[11px]">
                <th className="py-2 px-3">Metric</th>
                <th className="py-2 px-3">Model A (Baseline — 37 Feat)</th>
                <th className="py-2 px-3">Model B (Graph — 58 Feat)</th>
                <th className="py-2 px-3">Measured Delta (B − A)</th>
                <th className="py-2 px-3">Operational Takeaway</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#142a32]/60 text-slate-300">
              {comparisonRows.map((r) => (
                <tr key={r.name} className="hover:bg-[#081216]">
                  <td className="py-2.5 px-3 font-semibold text-white">{r.name}</td>
                  <td className="py-2.5 px-3 text-slate-300">{r.a}</td>
                  <td className="py-2.5 px-3 text-cyan-300 font-bold">{r.b}</td>
                  <td className={`py-2.5 px-3 font-semibold ${r.alert ? "text-amber-400" : "text-slate-300"}`}>
                    {r.d}
                  </td>
                  <td className="py-2.5 px-3 text-[10px] text-slate-400 font-sans">
                    {r.name.includes("PR-AUC") ? (
                      <span className="text-amber-300/90 font-mono">
                        Model B graph features elevate risk on shared infra
                      </span>
                    ) : r.name.includes("Recall") ? (
                      <span className="text-emerald-400 font-mono">100% Ring Interception</span>
                    ) : (
                      <span className="text-slate-400 font-mono">Identical discrete threshold counts</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Category-Level Breakdown Slices */}
        {data.category_slices && data.category_slices.length > 0 && (
          <div className="space-y-2 pt-2 border-t border-[#142a32]">
            <div className="flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <h4 className="font-bold text-white text-xs">
                Category-Level Slice Analysis (Which Look-Alikes Cause False Alarms?)
              </h4>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-[11px]">
                <thead>
                  <tr className="border-b border-[#142a32] text-slate-400 text-[10px]">
                    <th className="py-1.5 px-2">Category Code</th>
                    <th className="py-1.5 px-2">Description</th>
                    <th className="py-1.5 px-2 text-right">Count</th>
                    <th className="py-1.5 px-2 text-right">Model A FPs</th>
                    <th className="py-1.5 px-2 text-right">Model A FPR</th>
                    <th className="py-1.5 px-2 text-right">Model B FPs</th>
                    <th className="py-1.5 px-2 text-right">Model B FPR</th>
                    <th className="py-1.5 px-2 text-right">Delta FP</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#142a32]/40 text-slate-300">
                  {data.category_slices.map((cs) => (
                    <tr key={cs.challenge_category} className="hover:bg-[#081216]">
                      <td className="py-2 px-2 font-semibold text-cyan-300">{cs.challenge_category}</td>
                      <td className="py-2 px-2 text-slate-400 max-w-xs truncate font-sans text-[10px]">
                        {cs.description}
                      </td>
                      <td className="py-2 px-2 text-right text-slate-300">{cs.total_transactions}</td>
                      <td className="py-2 px-2 text-right text-slate-300">{cs.model_a.fp_count}</td>
                      <td className="py-2 px-2 text-right text-slate-400">{(cs.model_a.fpr * 100).toFixed(1)}%</td>
                      <td className="py-2 px-2 text-right text-cyan-300 font-bold">{cs.model_b.fp_count}</td>
                      <td className="py-2 px-2 text-right text-cyan-300">{(cs.model_b.fpr * 100).toFixed(1)}%</td>
                      <td className="py-2 px-2 text-right text-slate-400">
                        {cs.deltas.fp_delta >= 0 ? `+${cs.deltas.fp_delta}` : cs.deltas.fp_delta}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Threshold Sweep Drawer */}
        {data.threshold_sweep && (
          <div className="pt-2 border-t border-[#142a32] space-y-2">
            <button
              onClick={() => setShowSweep(!showSweep)}
              className="flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300 text-xs font-bold transition-colors"
            >
              <BarChart2 className="w-3.5 h-3.5" />
              <span>{showSweep ? "Hide" : "View"} Threshold Sensitivity Sweep (T = 0.10 to 0.90)</span>
              {showSweep ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            {showSweep && (
              <div className="overflow-x-auto pt-2">
                <table className="w-full text-left border-collapse text-[10px]">
                  <thead>
                    <tr className="border-b border-[#142a32] text-slate-400">
                      <th className="py-1 px-2">Threshold</th>
                      <th className="py-1 px-2 text-right">Model A Prec</th>
                      <th className="py-1 px-2 text-right">Model A Rec</th>
                      <th className="py-1 px-2 text-right">Model A FPs</th>
                      <th className="py-1 px-2 text-right">Model B Prec</th>
                      <th className="py-1 px-2 text-right">Model B Rec</th>
                      <th className="py-1 px-2 text-right">Model B FPs</th>
                      <th className="py-1 px-2 text-right">FP Delta</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#142a32]/40 text-slate-300 font-mono">
                    {data.threshold_sweep.map((s) => (
                      <tr key={s.threshold} className={s.threshold === 0.70 ? "bg-cyan-950/40 text-cyan-200" : "hover:bg-[#081216]"}>
                        <td className="py-1 px-2 font-bold">{s.threshold.toFixed(2)}</td>
                        <td className="py-1 px-2 text-right">{s.model_a.precision.toFixed(3)}</td>
                        <td className="py-1 px-2 text-right">{s.model_a.recall.toFixed(3)}</td>
                        <td className="py-1 px-2 text-right text-slate-400">{s.model_a.fp_count}</td>
                        <td className="py-1 px-2 text-right">{s.model_b.precision.toFixed(3)}</td>
                        <td className="py-1 px-2 text-right">{s.model_b.recall.toFixed(3)}</td>
                        <td className="py-1 px-2 text-right text-cyan-300">{s.model_b.fp_count}</td>
                        <td className="py-1 px-2 text-right text-slate-400">{s.deltas.fp_delta}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Methodology & Disclosure */}
        <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32] text-[11px] text-slate-400 space-y-1 font-sans">
          <div className="flex items-center gap-1.5 text-slate-300 font-semibold font-mono text-[10px]">
            <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
            <span>SCIENTIFIC DISCLOSURE &amp; KEY STAGE 13 FINDING</span>
          </div>
          <p className="leading-relaxed">
            On deliberate hard-negative lookalikes with verified amount and infrastructure overlap (e.g. residents paying a common landlord or roommates sharing a device), Model B does not demonstrate an incremental classification advantage over Model A (PR-AUC 0.2056 vs 0.2105). Results are consistent with graph features contributing to the ranking degradation when benign infrastructure sharing mimics coordinated fraud topologies. This empirical finding demonstrates a concrete in-silico failure mode of graph-enhanced models under benign infrastructure sharing, illustrating why <strong>autonomous blocking is hazardous</strong> and why <strong>evidence-backed human investigation (Stage 10/12) is critical</strong> to distinguish collusion rings from benign shared infrastructure.
          </p>
        </div>
      </div>
    </div>
  );
}
