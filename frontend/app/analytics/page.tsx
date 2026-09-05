"use client";

import { BarChart3, Database, ShieldAlert, CheckCircle2, Cpu } from "lucide-react";
import { ModelComparisonTable } from "@/components/analytics/ModelComparisonTable";
import { HardNegativeChallengePanel } from "@/components/analytics/HardNegativeChallengePanel";
import { FeatureDistributionChart } from "@/components/analytics/FeatureDistributionChart";
import { BusinessEconomicsPanel } from "@/components/analytics/BusinessEconomicsPanel";
import { CalibrationPanel } from "@/components/analytics/CalibrationPanel";
import { ThresholdPolicyPanel } from "@/components/analytics/ThresholdPolicyPanel";
import { ColdStartPanel } from "@/components/analytics/ColdStartPanel";
import { InvestigationEfficiencyPanel } from "@/components/analytics/InvestigationEfficiencyPanel";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6 select-none font-mono text-xs">
      {/* 1. Header Banner */}
      <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-2">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-cyan-400" />
          <h1 className="text-lg font-bold text-white font-sans tracking-wide">
            Model Performance &amp; Feature Analytics
          </h1>
        </div>
        <p className="text-slate-400 text-xs font-sans max-w-3xl leading-relaxed">
          Presents verified benchmark metrics from offline synthetic evaluation artifacts (Stages 6, 7, 13, &amp; 14). Compares Model A (Baseline 37 features) against Model B (Graph-Enhanced 58 features), robustness under hard negatives, probability calibration, and operational threshold policies.
        </p>
      </section>

      {/* 2. Feature Distribution Chart */}
      <FeatureDistributionChart />

      {/* 3. Held-Out Evaluation Benchmark Table (Truthful Delta: 0.0) */}
      <ModelComparisonTable />

      {/* 4. Hard-Negative Challenge Set (Robustness Stress Test - Stage 13) */}
      <HardNegativeChallengePanel />

      {/* 5. Post-Hoc Probability Calibration (Stage 14) */}
      <CalibrationPanel />

      {/* 6. Threshold Policy Optimization & Economic Sensitivity (Stage 14) */}
      <ThresholdPolicyPanel />

      {/* 7. Cold-Start Segmentation & Graph Confidence (Stage 14) */}
      <ColdStartPanel />

      {/* 7.5. Investigation Efficiency & Business Impact (Stage 15) */}
      <InvestigationEfficiencyPanel />

      {/* 8. Business Economics & ROI Modeling (Build Spec Section 21) */}
      <BusinessEconomicsPanel />

      {/* 4. Operational Value Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-[#081216] border border-[#142a32] space-y-2">
          <div className="flex items-center gap-2 font-bold text-white text-xs">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>Operational Role of Model A (37 Features)</span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
            Evaluates transaction-level parameters (amount, channel, time of day) and behavioral velocities (rolling 1h/24h/7d counts). Operates as a fast, localized first-pass risk check without network overhead.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#081216] border border-cyan-500/30 bg-[#08161d] space-y-2">
          <div className="flex items-center gap-2 font-bold text-cyan-300 text-xs">
            <ShieldAlert className="w-4 h-4 text-cyan-400" />
            <span>Operational Role of Model B (58 Features)</span>
          </div>
          <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
            Augments baseline features with 21 point-in-time graph metrics: degree centralities, co-usage clusters, and common recipient counts. Provides the rich topological context that feeds the Stage 9 Evidence Engine.
          </p>
        </div>
      </div>
    </div>
  );
}
