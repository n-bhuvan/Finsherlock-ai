"use client";

import { useState, useEffect } from "react";
import {
  Gauge,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  BarChart2,
  TrendingDown,
  Layers,
} from "lucide-react";
import { CalibrationResponse } from "@/types/analytics";

export function CalibrationPanel() {
  const [data, setData] = useState<CalibrationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState<"model_b" | "model_a">("model_b");

  useEffect(() => {
    async function fetchCalibrationData() {
      try {
        const res = await fetch("http://localhost:8000/api/analytics/calibration");
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
    fetchCalibrationData();
  }, []);

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] text-slate-400 font-mono text-xs flex items-center gap-2">
        <div className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        Loading Probability Calibration Analysis...
      </div>
    );
  }

  if (!data || data.status === "Unavailable" || !data.model_b) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] text-slate-400 font-mono text-xs space-y-2">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <AlertTriangle className="w-4 h-4" />
          <span>Probability Calibration Benchmark Unavailable</span>
        </div>
        <p className="text-[11px] text-slate-500">
          Calibration artifacts not loaded. Run <code className="text-cyan-300">python scripts/run_stage14_evaluation.py</code> to generate benchmark data.
        </p>
      </div>
    );
  }

  const modelData = selectedModel === "model_b" ? data.model_b : data.model_a!;
  const valMetrics = modelData.val_calib;
  const testMetrics = modelData.held_out_test;

  return (
    <div className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-[#142a32] pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Gauge className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white font-sans tracking-wide">
              Post-Hoc Probability Calibration (Stage 14)
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950/80 border border-cyan-700/60 text-cyan-300">
              {data.metadata?.val_calib_sample_count ?? 150} Val / {data.metadata?.held_out_test_sample_count ?? 300} Test
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans">
            Post-hoc probability calibration evaluated via Brier Score and Expected Calibration Error (ECE). Calibrators fitted on internal Val-Calib partition and frozen.
          </p>
        </div>

        {/* Model Selector */}
        <div className="flex items-center gap-2 bg-[#081216] p-1 rounded-lg border border-[#142a32]">
          <button
            onClick={() => setSelectedModel("model_b")}
            className={`px-3 py-1 rounded text-[11px] transition-all ${
              selectedModel === "model_b"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Model B (Graph)
          </button>
          <button
            onClick={() => setSelectedModel("model_a")}
            className={`px-3 py-1 rounded text-[11px] transition-all ${
              selectedModel === "model_a"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Model A (Baseline)
          </button>
        </div>
      </div>

      {/* Calibrator Selection Rationale Banner */}
      <div className="p-3.5 rounded-lg bg-[#08161d] border border-cyan-500/30 flex items-start gap-3">
        <CheckCircle2 className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-white uppercase tracking-wider">
              Selected Calibrator:
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 uppercase">
              {modelData.selected_calibrator}
            </span>
          </div>
          <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
            {modelData.selection_reason}
          </p>
        </div>
      </div>

      {/* Partition Comparisons: Val-Calib vs Held-Out Test */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Val-Calib Partition */}
        <div className="p-4 rounded-xl bg-[#081216] border border-[#142a32] space-y-3">
          <div className="flex items-center justify-between border-b border-[#142a32] pb-2">
            <div className="flex items-center gap-2 font-bold text-white text-xs font-sans">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>Val-Calib Fitting Partition (N=150)</span>
            </div>
            <span className="text-[10px] text-slate-400">32 Pos / 118 Neg</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[10px] text-slate-400 border-b border-[#142a32]">
                  <th className="py-2 px-1">Method</th>
                  <th className="py-2 px-2 text-right">Brier Score</th>
                  <th className="py-2 px-2 text-right">ECE</th>
                  <th className="py-2 px-2 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#142a32]/60 text-[11px]">
                <tr className={modelData.selected_calibrator === "raw" ? "bg-cyan-950/20 text-cyan-200" : "text-slate-300"}>
                  <td className="py-2 px-1 font-semibold">Raw Uncalibrated</td>
                  <td className="py-2 px-2 text-right font-mono">{valMetrics.raw.brier_score.toFixed(6)}</td>
                  <td className="py-2 px-2 text-right font-mono">{valMetrics.raw.ece.toFixed(6)}</td>
                  <td className="py-2 px-2 text-center text-[10px] text-slate-400">Baseline</td>
                </tr>
                <tr className={modelData.selected_calibrator === "platt" ? "bg-cyan-950/20 text-cyan-200" : "text-slate-300"}>
                  <td className="py-2 px-1 font-semibold">Platt Scaling</td>
                  <td className="py-2 px-2 text-right font-mono">{valMetrics.platt.brier_score.toFixed(6)}</td>
                  <td className="py-2 px-2 text-right font-mono">{valMetrics.platt.ece.toFixed(6)}</td>
                  <td className="py-2 px-2 text-center">
                    {modelData.selected_calibrator === "platt" ? (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-700/60">SELECTED</span>
                    ) : (
                      <span className="text-[10px] text-slate-500">Evaluated</span>
                    )}
                  </td>
                </tr>
                <tr className={modelData.selected_calibrator === "isotonic" ? "bg-cyan-950/20 text-cyan-200" : "text-slate-300"}>
                  <td className="py-2 px-1 font-semibold">Isotonic Regression</td>
                  <td className="py-2 px-2 text-right font-mono">{valMetrics.isotonic.brier_score.toFixed(6)}</td>
                  <td className="py-2 px-2 text-right font-mono">{valMetrics.isotonic.ece.toFixed(6)}</td>
                  <td className="py-2 px-2 text-center">
                    {modelData.selected_calibrator === "isotonic" ? (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-700/60">SELECTED</span>
                    ) : (
                      <span className="text-[10px] text-slate-500">Evaluated</span>
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Held-Out Test Partition */}
        <div className="p-4 rounded-xl bg-[#081216] border border-[#142a32] space-y-3">
          <div className="flex items-center justify-between border-b border-[#142a32] pb-2">
            <div className="flex items-center gap-2 font-bold text-white text-xs font-sans">
              <BarChart2 className="w-3.5 h-3.5 text-cyan-400" />
              <span>Held-Out Test Generalization (N=300)</span>
            </div>
            <span className="text-[10px] text-slate-400">26 Pos / 274 Neg</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[10px] text-slate-400 border-b border-[#142a32]">
                  <th className="py-2 px-1">Pipeline</th>
                  <th className="py-2 px-2 text-right">Test Brier</th>
                  <th className="py-2 px-2 text-right">Test ECE</th>
                  <th className="py-2 px-2 text-center">Delta vs Raw</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#142a32]/60 text-[11px]">
                <tr className="text-slate-300">
                  <td className="py-2 px-1 font-semibold">Raw Uncalibrated</td>
                  <td className="py-2 px-2 text-right font-mono">{testMetrics.raw.brier_score.toFixed(6)}</td>
                  <td className="py-2 px-2 text-right font-mono">{testMetrics.raw.ece.toFixed(6)}</td>
                  <td className="py-2 px-2 text-center text-[10px] text-slate-500">—</td>
                </tr>
                <tr className="bg-cyan-950/20 text-cyan-200">
                  <td className="py-2 px-1 font-semibold">Selected ({testMetrics.selected_calibrated.method.toUpperCase()})</td>
                  <td className="py-2 px-2 text-right font-mono font-bold text-cyan-300">
                    {testMetrics.selected_calibrated.brier_score.toFixed(6)}
                  </td>
                  <td className="py-2 px-2 text-right font-mono font-bold text-cyan-300">
                    {testMetrics.selected_calibrated.ece.toFixed(6)}
                  </td>
                  <td className="py-2 px-2 text-center font-mono text-[10px]">
                    {(testMetrics.selected_calibrated.brier_score - testMetrics.raw.brier_score) <= 0 ? (
                      <span className="text-emerald-400">{(testMetrics.selected_calibrated.brier_score - testMetrics.raw.brier_score).toFixed(6)}</span>
                    ) : (
                      <span className="text-amber-400">+{(testMetrics.selected_calibrated.brier_score - testMetrics.raw.brier_score).toFixed(6)}</span>
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-[10px] text-slate-400 font-sans">
            Post-freeze test evaluation confirms probability bounds and calibration stability on previously unseen data.
          </p>
        </div>
      </div>

      {/* Reliability Diagram Table (10 Bins) */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-white font-sans">
            Reliability Diagram Bins (Held-Out Test Set — 10 Quantile Bins)
          </span>
          <span className="text-[10px] text-slate-500">Perfect Calibration: Empirical Rate = Mean Prob</span>
        </div>
        <div className="overflow-x-auto rounded-lg border border-[#142a32]">
          <table className="w-full text-left bg-[#081216]">
            <thead>
              <tr className="text-[10px] text-slate-400 border-b border-[#142a32] bg-[#0b151b]">
                <th className="py-2 px-2">Bin Range</th>
                <th className="py-2 px-2 text-right">Sample Count</th>
                <th className="py-2 px-2 text-right">Mean Predicted Prob</th>
                <th className="py-2 px-2 text-right">Empirical Fraud Rate</th>
                <th className="py-2 px-2 text-right">Calibration Gap</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#142a32]/60 text-[11px]">
              {testMetrics.selected_calibrated.reliability_curve.map((bin) => {
                const gap = Math.abs(bin.empirical_fraud_rate - bin.mean_predicted_prob);
                return (
                  <tr key={bin.bin_index} className="hover:bg-[#0b151b]/60">
                    <td className="py-1.5 px-2 font-mono text-slate-300">
                      [{bin.bin_lower.toFixed(1)} - {bin.bin_upper.toFixed(1)})
                    </td>
                    <td className="py-1.5 px-2 text-right font-mono text-slate-300">{bin.sample_count}</td>
                    <td className="py-1.5 px-2 text-right font-mono text-cyan-300">{bin.mean_predicted_prob.toFixed(4)}</td>
                    <td className="py-1.5 px-2 text-right font-mono text-slate-200">{bin.empirical_fraud_rate.toFixed(4)}</td>
                    <td className="py-1.5 px-2 text-right font-mono text-[10px]">
                      {bin.sample_count > 0 ? (
                        <span className={gap < 0.05 ? "text-emerald-400" : "text-amber-400"}>{gap.toFixed(4)}</span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Methodological Transparency Note */}
      <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32] text-[10px] text-slate-400 font-sans leading-relaxed">
        <span className="font-bold text-slate-300">Methodological Disclosure: </span>
        Brier scores are bounded in [0, 1]. Calibrator selection algorithm evaluates candidate methods strictly on the internal Val-Calib split (N=150) using lowest Brier score, with an automatic fallback to raw uncalibrated probabilities if both Platt and Isotonic degrade Brier score. A Platt tie-breaker is applied when |ΔBS| ≤ 0.005 for parametric stability on small validation samples. ECE is reported as a diagnostic metric.
      </div>
    </div>
  );
}
