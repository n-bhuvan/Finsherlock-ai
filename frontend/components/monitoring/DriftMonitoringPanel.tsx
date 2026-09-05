"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Radio,
  BarChart3,
  Calendar,
  Layers,
  HelpCircle,
} from "lucide-react";
import {
  DriftMonitoringResponse,
  DriftStatus,
  DriftMetric,
} from "@/types/monitoring";
import { getDriftMonitoring } from "@/lib/api";

export function DriftMonitoringPanel() {
  const [driftData, setDriftData] = useState<DriftMonitoringResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refWindow, setRefWindow] = useState<string>("train");
  const [compWindow, setCompWindow] = useState<string>("test");

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    getDriftMonitoring(refWindow, compWindow)
      .then((res) => {
        if (isMounted && res.data) {
          setDriftData(res.data);
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [refWindow, compWindow]);

  const getStatusBadge = (status: DriftStatus) => {
    switch (status) {
      case "NORMAL":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold text-[10px]">
            <CheckCircle2 className="w-3 h-3" />
            NORMAL
          </span>
        );
      case "WATCH":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold text-[10px]">
            <AlertTriangle className="w-3 h-3" />
            WATCH
          </span>
        );
      case "SIGNIFICANT_DRIFT":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 font-bold text-[10px]">
            <XCircle className="w-3 h-3" />
            SIGNIFICANT DRIFT
          </span>
        );
      case "UNAVAILABLE":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-500/10 border border-slate-500/30 text-slate-400 font-bold text-[10px]">
            <HelpCircle className="w-3 h-3" />
            UNAVAILABLE
          </span>
        );
    }
  };

  return (
    <div className="rounded-xl bg-[#081216] border border-[#142a32] shadow-2xl overflow-hidden font-mono text-xs">
      {/* Header Banner */}
      <div className="px-5 py-4 bg-[#0b181f] border-b border-[#142a32] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-cyan-950/60 border border-cyan-500/30 rounded-lg">
            <Radio className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-white tracking-wide">
                Distribution Drift &amp; Stability Monitoring
              </h2>
              <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-[10px] font-bold">
                STAGE 20
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Deterministic Population Stability Index (PSI), Jensen-Shannon Divergence (JSD), and Missingness Shift
            </p>
          </div>
        </div>

        {/* Window Selector */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-[10px]">Reference:</span>
          <select
            value={refWindow}
            onChange={(e) => setRefWindow(e.target.value)}
            className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
          >
            <option value="train">Train (N=1400)</option>
            <option value="val">Validation (N=300)</option>
          </select>

          <span className="text-slate-400 text-[10px]">Comparison:</span>
          <select
            value={compWindow}
            onChange={(e) => setCompWindow(e.target.value)}
            className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
          >
            <option value="test">Held-out Test (N=300)</option>
            <option value="val">Validation (N=300)</option>
          </select>
        </div>
      </div>

      {/* Main Container */}
      <div className="p-5 space-y-5">
        {loading ? (
          <div className="py-10 text-center text-slate-400 animate-pulse flex items-center justify-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400 animate-spin" />
            Computing statistical distribution drift...
          </div>
        ) : !driftData ? (
          <div className="py-6 text-center text-slate-500">
            Drift monitoring telemetry unavailable.
          </div>
        ) : (
          <>
            {/* Top Stat Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Overall Drift Status */}
              <div className="p-3.5 rounded-lg bg-[#0c1820] border border-[#183440] space-y-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                  Overall Drift Status
                </div>
                <div>{getStatusBadge(driftData.overall_status)}</div>
              </div>

              {/* Monitored Features Count */}
              <div className="p-3.5 rounded-lg bg-[#0c1820] border border-[#183440] space-y-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                  Features Evaluated
                </div>
                <div className="text-base font-bold text-white">
                  {driftData.metrics.length} Monitored Signals
                </div>
              </div>

              {/* Significant Drift Features */}
              <div className="p-3.5 rounded-lg bg-[#0c1820] border border-[#183440] space-y-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                  Significant Drift Flags
                </div>
                <div className="text-base font-bold text-rose-400">
                  {driftData.significant_features.length} Features
                </div>
              </div>

              {/* Watch Features */}
              <div className="p-3.5 rounded-lg bg-[#0c1820] border border-[#183440] space-y-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                  Watch Status Flags
                </div>
                <div className="text-base font-bold text-amber-400">
                  {driftData.watch_features.length} Features
                </div>
              </div>
            </div>

            {/* 15 Monitored Feature Drift Table */}
            <div className="border border-[#142a32] rounded-lg overflow-hidden">
              <div className="px-4 py-2.5 bg-[#09151b] border-b border-[#142a32] flex items-center justify-between">
                <span className="font-bold text-white text-[11px] uppercase tracking-wider">
                  Monitored Feature Distribution Metrics
                </span>
                <span className="text-[10px] text-slate-400">
                  PSI &lt; 0.10 Normal | 0.10-0.25 Watch | &ge; 0.25 Significant Drift
                </span>
              </div>
              <div className="overflow-x-auto max-h-[380px] overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#0b171d] text-slate-400 text-[10px] uppercase border-b border-[#142a32] sticky top-0">
                    <tr>
                      <th className="px-4 py-2">Feature Name</th>
                      <th className="px-3 py-2">Metric Type</th>
                      <th className="px-3 py-2">Drift Value</th>
                      <th className="px-3 py-2">Thresholds (Watch / Sig)</th>
                      <th className="px-3 py-2">Status</th>
                      <th className="px-3 py-2">Limitations</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#102229]">
                    {driftData.metrics.map((m) => (
                      <tr
                        key={m.feature_name}
                        className={`hover:bg-[#0c1b22] transition-colors ${
                          m.status === "SIGNIFICANT_DRIFT"
                            ? "bg-rose-950/10"
                            : m.status === "WATCH"
                            ? "bg-amber-950/10"
                            : ""
                        }`}
                      >
                        <td className="px-4 py-2 font-mono text-cyan-300 font-medium">
                          {m.feature_name}
                        </td>
                        <td className="px-3 py-2 text-slate-300">{m.metric_name}</td>
                        <td className="px-3 py-2 font-mono font-bold text-white">
                          {m.metric_value.toFixed(4)}
                        </td>
                        <td className="px-3 py-2 text-slate-400 text-[10px]">
                          {m.threshold_watch.toFixed(2)} / {m.threshold_significant.toFixed(2)}
                        </td>
                        <td className="px-3 py-2">{getStatusBadge(m.status)}</td>
                        <td className="px-3 py-2 text-[10px] text-slate-400 truncate max-w-xs">
                          {m.limitations || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Performance Comparison Panel where ground truth exists */}
            {driftData.performance_comparison && (
              <div className="border border-[#142a32] rounded-lg overflow-hidden">
                <div className="px-4 py-2.5 bg-[#09151b] border-b border-[#142a32]">
                  <span className="font-bold text-white text-[11px] uppercase tracking-wider">
                    Model Performance Shift (Synthetic Evaluation Partitions)
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#142a32]">
                  {Object.entries(driftData.performance_comparison).map(([winKey, perf]) => (
                    <div key={winKey} className="p-4 space-y-2 bg-[#0a141a]">
                      <div className="flex items-center justify-between text-xs font-bold text-cyan-300 uppercase">
                        <span>Window: {winKey}</span>
                        <span className="text-slate-400 font-normal text-[10px]">
                          N = {perf.sample_size}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-center text-[11px] pt-1">
                        <div className="p-2 rounded bg-black/30 border border-slate-800">
                          <div className="text-slate-400 text-[9px] uppercase">Precision</div>
                          <div className="font-bold text-white mt-0.5">
                            {typeof perf.precision === "number" ? `${(perf.precision * 100).toFixed(1)}%` : "N/A"}
                          </div>
                        </div>
                        <div className="p-2 rounded bg-black/30 border border-slate-800">
                          <div className="text-slate-400 text-[9px] uppercase">Recall</div>
                          <div className="font-bold text-white mt-0.5">
                            {typeof perf.recall === "number" ? `${(perf.recall * 100).toFixed(1)}%` : "N/A"}
                          </div>
                        </div>
                        <div className="p-2 rounded bg-black/30 border border-slate-800">
                          <div className="text-slate-400 text-[9px] uppercase">Brier Loss</div>
                          <div className="font-bold text-white mt-0.5">
                            {typeof perf.brier_score === "number" ? perf.brier_score.toFixed(4) : "N/A"}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Governance & Non-Autonomous Notice */}
            <div className="p-3 rounded-lg bg-[#071014] border border-[#14262f] space-y-1 text-[11px] text-slate-400 font-sans">
              <div className="flex items-center gap-2 text-cyan-400 font-bold font-mono text-[10px] uppercase">
                <Layers className="w-3.5 h-3.5" />
                SIMULATED / SYNTHETIC BENCHMARK — HUMAN DECISION SUPPORT
              </div>
              <p className="leading-relaxed">
                {driftData.disclaimer} Drift alerts advise human investigation priority review;
                they never trigger automated retraining, threshold mutations, or autonomous customer enforcement.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
