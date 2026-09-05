"use client";

import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ShieldCheck,
  Activity,
  Layers,
} from "lucide-react";
import { OutcomeVerificationResponse, OutcomeStatus } from "@/types/monitoring";
import { getTransactionOutcome } from "@/lib/api";

interface Props {
  transactionId: string;
}

export function OutcomeVerificationPanel({ transactionId }: Props) {
  const [outcome, setOutcome] = useState<OutcomeVerificationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [context, setContext] = useState<string>("SIMULATED_BENCHMARK");

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    getTransactionOutcome(transactionId, context)
      .then((res) => {
        if (isMounted && res.data) {
          setOutcome(res.data);
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [transactionId, context]);

  const getStatusBadge = (status: OutcomeStatus) => {
    switch (status) {
      case "OUTCOME_CONFIRMED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold text-xs tracking-wider">
            <CheckCircle2 className="w-3.5 h-3.5" />
            OUTCOME CONFIRMED
          </span>
        );
      case "OUTCOME_UNAVAILABLE":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-500/10 border border-slate-500/30 text-slate-400 font-bold text-xs tracking-wider">
            <HelpCircle className="w-3.5 h-3.5" />
            OUTCOME UNAVAILABLE
          </span>
        );
      case "OUTCOME_PENDING":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold text-xs tracking-wider">
            <AlertTriangle className="w-3.5 h-3.5" />
            OUTCOME PENDING
          </span>
        );
      case "OUTCOME_INCONCLUSIVE":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 font-bold text-xs tracking-wider">
            <XCircle className="w-3.5 h-3.5" />
            INCONCLUSIVE
          </span>
        );
    }
  };

  return (
    <div className="rounded-xl bg-[#081216] border border-[#142a32] shadow-2xl overflow-hidden font-mono text-xs">
      {/* Header Banner */}
      <div className="px-5 py-3.5 bg-[#0b181f] border-b border-[#142a32] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-cyan-950/60 border border-cyan-500/30 rounded-lg">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-white tracking-wide">
                Post-Decision Outcome Verification
              </h2>
              <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-[10px] font-bold">
                STAGE 20
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Audit telemetry separating Prediction vs Policy Recommendation vs Observed Outcome
            </p>
          </div>
        </div>

        {/* Evaluation Context Switcher */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setContext("SIMULATED_BENCHMARK")}
            className={`px-2.5 py-1 rounded text-[11px] font-bold border transition-colors ${
              context === "SIMULATED_BENCHMARK"
                ? "bg-cyan-950/80 border-cyan-500/50 text-cyan-300 shadow"
                : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
            }`}
          >
            SIMULATED BENCHMARK
          </button>
          <button
            onClick={() => setContext("OPERATIONAL")}
            className={`px-2.5 py-1 rounded text-[11px] font-bold border transition-colors ${
              context === "OPERATIONAL"
                ? "bg-cyan-950/80 border-cyan-500/50 text-cyan-300 shadow"
                : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
            }`}
          >
            OPERATIONAL CONTEXT
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-5 space-y-4">
        {loading ? (
          <div className="py-8 text-center text-slate-400 animate-pulse flex items-center justify-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400 animate-spin" />
            Loading outcome verification telemetry...
          </div>
        ) : !outcome ? (
          <div className="py-6 text-center text-slate-500">
            No outcome verification data available for this case.
          </div>
        ) : (
          <>
            {/* Top Stat Ribbon */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* 1. Prediction at Decision */}
              <div className="p-3.5 rounded-lg bg-[#0c1820] border border-[#183440] space-y-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                  Prediction at Decision
                </div>
                <div className="text-base font-bold text-white flex items-baseline gap-1.5">
                  {outcome.prediction_at_decision !== null && outcome.prediction_at_decision !== undefined
                    ? `${(outcome.prediction_at_decision * 100).toFixed(1)}%`
                    : "N/A"}
                  <span className="text-[10px] text-slate-400 font-normal">calibrated risk</span>
                </div>
              </div>

              {/* 2. Policy Recommendation */}
              <div className="p-3.5 rounded-lg bg-[#0c1820] border border-[#183440] space-y-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                  Policy Recommendation
                </div>
                <div className="text-base font-bold text-cyan-400">
                  {outcome.policy_action_at_decision || "N/A"}
                </div>
              </div>

              {/* 3. Observed Outcome */}
              <div className="p-3.5 rounded-lg bg-[#0c1820] border border-[#183440] space-y-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                  Observed Outcome
                </div>
                <div className="text-base font-bold text-white uppercase">
                  {outcome.observed_outcome || "UNAVAILABLE"}
                </div>
              </div>

              {/* 4. Outcome Status */}
              <div className="p-3.5 rounded-lg bg-[#0c1820] border border-[#183440] space-y-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                  Verification State
                </div>
                <div>{getStatusBadge(outcome.outcome_status)}</div>
              </div>
            </div>

            {/* Match / Alignment Card */}
            {outcome.outcome_status === "OUTCOME_CONFIRMED" ? (
              <div
                className={`p-3.5 rounded-lg border flex items-center justify-between gap-3 ${
                  outcome.outcome_match
                    ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
                    : "bg-amber-950/20 border-amber-500/30 text-amber-300"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  {outcome.outcome_match ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
                  )}
                  <div>
                    <span className="font-bold text-xs">
                      {outcome.outcome_match
                        ? "PREDICTION / OUTCOME ALIGNED (MATCH)"
                        : "DISCREPANCY DETECTED (MISMATCH)"}
                    </span>
                    <p className="text-[11px] text-slate-300/80 font-sans mt-0.5">
                      {outcome.outcome_match
                        ? `Calibrated risk of ${((outcome.prediction_at_decision || 0) * 100).toFixed(1)}% and policy action ${outcome.policy_action_at_decision} concurred with verified ${outcome.observed_outcome} outcome.`
                        : `Decision context indicated non-standard distribution alignment against verified ${outcome.observed_outcome} outcome.`}
                    </p>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded bg-black/40 text-[10px] font-mono font-bold text-slate-300">
                  SOURCE: {outcome.verification_source}
                </span>
              </div>
            ) : (
              <div className="p-3.5 rounded-lg bg-slate-900/50 border border-slate-800 text-slate-400 flex items-center gap-2.5">
                <HelpCircle className="w-5 h-5 text-slate-500 flex-shrink-0" />
                <span className="text-[11px] font-sans">
                  {outcome.limitations}
                </span>
              </div>
            )}

            {/* Disclaimer & Governance Notice */}
            <div className="p-3 rounded-lg bg-[#071014] border border-[#14262f] space-y-1 text-[11px] text-slate-400 font-sans">
              <div className="flex items-center gap-2 text-cyan-400 font-bold font-mono text-[10px] uppercase">
                <Layers className="w-3.5 h-3.5" />
                SIMULATED / SYNTHETIC BENCHMARK — NON-CAUSAL DECISION SUPPORT
              </div>
              <p className="leading-relaxed">
                {outcome.disclaimer} Observed outcomes do not assert causal fraud prevention and
                never modify model weights, calibrator curves, or historical risk scores.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
