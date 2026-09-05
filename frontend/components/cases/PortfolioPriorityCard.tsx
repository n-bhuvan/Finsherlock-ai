"use client";

import { useEffect, useState } from "react";
import {
  TrendingUp,
  AlertCircle,
  HelpCircle,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Coins,
  Scale,
  ArrowRight,
  Info,
} from "lucide-react";
import { PrioritizedCaseItem } from "@/types/prioritization";
import { getPortfolioCasePrioritization } from "@/lib/api";

interface PortfolioPriorityCardProps {
  transactionId: string;
}

export function PortfolioPriorityCard({ transactionId }: PortfolioPriorityCardProps) {
  const [data, setData] = useState<PrioritizedCaseItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getPortfolioCasePrioritization(transactionId).then((res) => {
      if (!isMounted) return;
      if (res.data) {
        setData(res.data);
      } else {
        setError(res.error || "Failed to load portfolio prioritization.");
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
        <TrendingUp className="w-4 h-4 text-cyan-400 animate-spin" />
        <span>Calculating portfolio priority score and decision-theoretic expected value...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-slate-800 text-slate-400 font-mono text-xs flex items-center gap-2">
        <Info className="w-4 h-4 text-slate-500 shrink-0" />
        <span>Portfolio Prioritization: {error || "Unavailable"}</span>
      </div>
    );
  }

  const isPositiveEV = data.expected_value > 0;

  return (
    <div className="rounded-xl bg-[#0b151b] border border-[#142a32] overflow-hidden shadow-xl">
      {/* Header Banner */}
      <div className="p-4 sm:p-5 border-b border-[#142a32] bg-[#071015]/70 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <Scale className="w-5 h-5 text-cyan-400" />
            <h3 className="font-semibold text-white text-base">
              Portfolio Risk Prioritization & Expected Value
            </h3>
            <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-cyan-950 border border-cyan-500/40 text-cyan-300">
              V2 Stage 16
            </span>
            <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-900 border border-slate-700 text-slate-400">
              Deterministic Decision Theory
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Answers &ldquo;Why investigate this case before another?&rdquo; by computing expected prevented loss minus friction and operational costs.
          </p>
        </div>

        {/* Priority Score & Rank Callout */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="text-right">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">
              Priority Score
            </div>
            <div className="text-2xl font-mono font-bold text-cyan-300">
              {(data.priority_score * 100).toFixed(1)}%
            </div>
          </div>

          <div className="pl-3 border-l border-[#142a32] text-right">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">
              Investigation Priority
            </div>
            <span
              className={`inline-block px-2.5 py-1 text-xs font-bold rounded ${
                data.recommended_action === "PRIORITIZE_INVESTIGATION"
                  ? "bg-rose-950/80 border border-rose-500/50 text-rose-300"
                  : data.recommended_action === "HIGH_PRIORITY_REVIEW"
                  ? "bg-amber-950/80 border border-amber-500/50 text-amber-300"
                  : data.recommended_action === "REVIEW_NEXT"
                  ? "bg-cyan-950/80 border border-cyan-500/50 text-cyan-300"
                  : data.recommended_action === "LOW_PRIORITY"
                  ? "bg-slate-900 border border-slate-700 text-slate-400"
                  : "bg-slate-950 border border-slate-800 text-slate-500"
              }`}
            >
              {data.recommended_action.replace(/_/g, " ")}
            </span>
          </div>
        </div>
      </div>

      {/* Rationale: "Why investigate this case?" */}
      <div className="p-4 sm:p-5 border-b border-[#142a32] bg-[#071015]/40">
        <div className="flex items-center gap-2 mb-1.5 text-xs font-semibold text-slate-200 uppercase tracking-wider">
          <HelpCircle className="w-4 h-4 text-cyan-400" />
          <span>Why Investigate This Case?</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed bg-[#0b151b] p-3 rounded-lg border border-[#142a32]">
          {data.priority_reason}
        </p>
      </div>

      {/* Decision-Theoretic Expected Value Breakdown (4 Metric Grid) */}
      <div className="p-4 sm:p-5 grid grid-cols-2 lg:grid-cols-4 gap-4 border-b border-[#142a32]">
        {/* Metric 1: Expected Loss Avoided */}
        <div className="p-3 rounded-lg bg-[#071015]/80 border border-[#142a32]">
          <div className="text-[10px] text-slate-400 uppercase font-mono tracking-wider">
            Expected Loss Avoided
          </div>
          <div className="text-base font-mono font-bold text-emerald-400 mt-1">
            +₹{data.expected_loss_avoided.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            p_calib × Exp × 85%
          </div>
        </div>

        {/* Metric 2: Expected Friction Cost */}
        <div className="p-3 rounded-lg bg-[#071015]/80 border border-[#142a32]">
          <div className="text-[10px] text-slate-400 uppercase font-mono tracking-wider">
            Customer Friction Cost
          </div>
          <div className="text-base font-mono font-bold text-rose-400 mt-1">
            -₹{data.friction_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            (1 - p_calib) × ₹1,200
          </div>
        </div>

        {/* Metric 3: Human Investigation Cost */}
        <div className="p-3 rounded-lg bg-[#071015]/80 border border-[#142a32]">
          <div className="text-[10px] text-slate-400 uppercase font-mono tracking-wider">
            Investigation Review Cost
          </div>
          <div className="text-base font-mono font-bold text-slate-300 mt-1">
            -₹{data.investigation_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Fixed operational cost Cinv
          </div>
        </div>

        {/* Metric 4: Net Expected Value */}
        <div className="p-3 rounded-lg bg-[#071015]/80 border border-[#142a32]">
          <div className="text-[10px] text-slate-400 uppercase font-mono tracking-wider">
            Net Expected Value
          </div>
          <div
            className={`text-base font-mono font-bold mt-1 ${
              isPositiveEV ? "text-cyan-300" : "text-amber-400"
            }`}
          >
            {isPositiveEV ? "+" : ""}₹{data.expected_value.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            EVnorm: {(data.ev_normalized * 100).toFixed(1)}% (cap ₹85k)
          </div>
        </div>
      </div>

      {/* Input Signals Table */}
      <div className="p-4 sm:p-5 border-b border-[#142a32] bg-[#071015]/20">
        <div className="text-xs font-semibold text-slate-300 mb-3 flex items-center justify-between">
          <span>Priority Scoring Components (Weights sum to 100%)</span>
          <span className="text-[10px] font-mono text-cyan-400/80">
            Priority Score: {(data.priority_score * 100).toFixed(1)}%
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-center font-mono">
          <div className="p-2 rounded bg-[#071015] border border-slate-800">
            <span className="text-[9px] text-slate-400 block">Risk (25%)</span>
            <span className="text-xs text-white font-bold">{(data.risk_score * 100).toFixed(1)}%</span>
          </div>

          <div className="p-2 rounded bg-[#071015] border border-slate-800">
            <span className="text-[9px] text-slate-400 block">EV Norm (25%)</span>
            <span className="text-xs text-white font-bold">{(data.ev_normalized * 100).toFixed(1)}%</span>
          </div>

          <div className="p-2 rounded bg-[#071015] border border-slate-800">
            <span className="text-[9px] text-slate-400 block">Exposure (15%)</span>
            <span className="text-xs text-white font-bold">₹{data.exposure.toLocaleString("en-IN")}</span>
          </div>

          <div className="p-2 rounded bg-[#071015] border border-slate-800">
            <span className="text-[9px] text-slate-400 block">Net Leverage (15%)</span>
            <span className="text-xs text-white font-bold">{(data.network_leverage * 100).toFixed(0)}%</span>
          </div>

          <div className="p-2 rounded bg-[#071015] border border-slate-800">
            <span className="text-[9px] text-slate-400 block">Systemic Anom (10%)</span>
            <span className="text-xs text-white font-bold">{(data.systemic_anomaly_score * 100).toFixed(1)}%</span>
          </div>

          <div className="p-2 rounded bg-[#071015] border border-slate-800">
            <span className="text-[9px] text-slate-400 block">Uncertainty (10%)</span>
            <span className="text-xs text-white font-bold">{(data.investigative_uncertainty * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Simulated Economic Estimate Disclaimer */}
      <div className="p-3.5 bg-[#071015] flex items-start gap-2.5 text-[11px] text-slate-400">
        <Coins className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div className="flex-1">
          <span className="font-semibold text-slate-300">Simulated Economic Estimate Disclaimer: </span>
          <span>{data.synthetic_monetary_value_disclaimer}</span>
        </div>
      </div>
    </div>
  );
}
