"use client";

import React from "react";
import { Radio, ShieldAlert, Cpu } from "lucide-react";
import { DriftMonitoringPanel } from "@/components/monitoring/DriftMonitoringPanel";

export default function MonitoringPage() {
  return (
    <div className="space-y-6 select-none font-mono text-xs">
      {/* 1. Header Banner */}
      <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-2">
        <div className="flex items-center gap-2">
          <Radio className="w-5 h-5 text-cyan-400" />
          <h1 className="text-lg font-bold text-white font-sans tracking-wide">
            Model Context &amp; Distribution Drift Monitoring
          </h1>
          <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-[10px] font-bold">
            STAGE 20
          </span>
        </div>
        <p className="text-slate-400 text-xs font-sans max-w-3xl leading-relaxed">
          Monitors distribution shifts across 15 core financial, behavioral, topological, and model-context features using deterministic Population Stability Index (PSI), Jensen-Shannon Divergence (JSD), and missingness tracking.
        </p>
      </section>

      {/* 2. Main Drift Monitoring Panel */}
      <DriftMonitoringPanel />
    </div>
  );
}
