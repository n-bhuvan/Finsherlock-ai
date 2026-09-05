"use client";

import { useEffect, useState } from "react";
import {
  Compass,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  HelpCircle,
  TrendingDown,
  DollarSign,
  Cpu,
  Layers,
  Sparkles,
  ArrowRight,
  Clock,
  Check,
} from "lucide-react";
import {
  InvestigationStateResponse,
  StoppingReason,
  NextBestActionType,
} from "@/types/investigation";
import { getInvestigationState, runBoundedInvestigation } from "@/lib/api";

interface InvestigationAgentPanelProps {
  transactionId: string;
}

export function InvestigationAgentPanel({ transactionId }: InvestigationAgentPanelProps) {
  const [state, setState] = useState<InvestigationStateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getInvestigationState(transactionId).then((res) => {
      if (!isMounted) return;
      if (res.data) {
        setState(res.data);
      } else {
        setError(res.error || "Failed to load investigation state.");
      }
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [transactionId]);

  const handleRunInvestigation = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await runBoundedInvestigation({
        transaction_id: transactionId,
        max_steps: 5,
        tool_budget: 150.0,
      });
      if (res.data) {
        setState(res.data);
      } else {
        setError(res.error || "Failed to execute bounded investigation.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to run investigation.");
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] font-mono text-xs text-slate-400 animate-pulse flex items-center gap-2">
        <Compass className="w-4 h-4 text-cyan-400 animate-spin" />
        Evaluating investigative uncertainty &amp; candidate tools...
      </div>
    );
  }

  if (error && !state) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-rose-900/50 text-rose-300 font-mono text-xs">
        <div className="flex items-center gap-2 font-bold mb-1">
          <AlertTriangle className="w-4 h-4 text-rose-400" />
          Investigation Agent Error
        </div>
        <p>{error}</p>
      </div>
    );
  }

  if (!state) return null;

  // Stopping reason badge colors
  const getStoppingBadge = (reason: StoppingReason) => {
    switch (reason) {
      case "SUFFICIENT_EVIDENCE":
        return { bg: "bg-emerald-950/70 border-emerald-800 text-emerald-300", label: "Sufficient Evidence Gathered" };
      case "UNCERTAINTY_LOW_ENOUGH":
        return { bg: "bg-cyan-950/70 border-cyan-800 text-cyan-300", label: "Target Uncertainty Reached" };
      case "INVESTIGATION_COST_TOO_HIGH":
        return { bg: "bg-amber-950/70 border-amber-800 text-amber-300", label: "Tool Budget Limit Reached" };
      case "MAX_INVESTIGATION_STEPS":
        return { bg: "bg-blue-950/70 border-blue-800 text-blue-300", label: "Max Steps Completed (5/5)" };
      case "CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW":
        return { bg: "bg-rose-950/70 border-rose-800 text-rose-300", label: "Conflicting Evidence Detected" };
      case "EVIDENCE_EXHAUSTED":
        return { bg: "bg-slate-900 border-slate-700 text-slate-300", label: "All Candidate Tools Executed" };
      case "INFORMATION_GAIN_TOO_LOW":
        return { bg: "bg-amber-950/70 border-amber-800 text-amber-300", label: "Information Gain Below Threshold" };
      default:
        return { bg: "bg-slate-900 border-slate-700 text-slate-400", label: reason };
    }
  };

  // Action badge styling
  const getActionBadge = (action: NextBestActionType) => {
    switch (action) {
      case "HOLD_FOR_REVIEW":
        return "bg-rose-950/80 border-rose-600 text-rose-200";
      case "ESCALATE_TO_ANALYST":
        return "bg-purple-950/80 border-purple-600 text-purple-200";
      case "REQUEST_ADDITIONAL_VERIFICATION":
        return "bg-amber-950/80 border-amber-600 text-amber-200";
      case "ALLOW":
        return "bg-emerald-950/80 border-emerald-600 text-emerald-200";
      case "MONITOR":
      default:
        return "bg-cyan-950/80 border-cyan-600 text-cyan-200";
    }
  };

  const stoppingBadge = getStoppingBadge(state.stopping_reason);

  return (
    <div className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-2xl space-y-5 font-mono text-xs">
      {/* 1. Panel Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#142a32]">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-cyan-400" />
            <h2 className="text-sm font-bold text-white tracking-wide uppercase font-sans">
              Bounded Uncertainty-Driven Investigation Agent
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950/70 border border-cyan-800 text-cyan-300">
              STAGE 15
            </span>
          </div>
          <p className="text-slate-400 text-[11px] font-sans">
            Deterministic Expected Information Gain heuristic • Granular simulated tool budgeting • Explicit stopping policy
          </p>
        </div>

        <button
          onClick={handleRunInvestigation}
          disabled={running}
          className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 active:bg-cyan-700 text-white font-bold transition disabled:opacity-50 text-[11px] shadow-lg shadow-cyan-950/50 cursor-pointer"
        >
          {running ? (
            <>
              <Compass className="w-3.5 h-3.5 animate-spin" />
              <span>Investigating...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>Run Bounded Investigation</span>
            </>
          )}
        </button>
      </div>

      {/* 2. Key Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {/* Calibrated Risk */}
        <div className="p-3 rounded-lg bg-[#071115] border border-[#142a32] space-y-1">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Calibrated Risk</span>
          <div className="text-base font-bold text-white font-sans flex items-center gap-1.5">
            <span className={state.calibrated_risk >= 0.7 ? "text-rose-400" : state.calibrated_risk >= 0.2 ? "text-amber-400" : "text-emerald-400"}>
              {(state.calibrated_risk * 100).toFixed(1)}%
            </span>
            <span className="text-[10px] text-slate-500 font-mono">({state.graph_confidence})</span>
          </div>
        </div>

        {/* Investigative Uncertainty */}
        <div className="p-3 rounded-lg bg-[#071115] border border-[#142a32] space-y-1">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Uncertainty (U)</span>
          <div className="text-base font-bold text-white font-sans flex items-center gap-1">
            <span className="text-slate-400 font-mono text-xs">{state.initial_uncertainty.toFixed(3)}</span>
            <ArrowRight className="w-3 h-3 text-cyan-400" />
            <span className="text-cyan-300 font-mono">{state.current_uncertainty.toFixed(3)}</span>
          </div>
          <span className="text-[10px] text-emerald-400 block font-mono">
            &Delta; -{(state.total_uncertainty_reduction * 100).toFixed(1)}%
          </span>
        </div>

        {/* Triage Priority Score */}
        <div className="p-3 rounded-lg bg-[#071115] border border-[#142a32] space-y-1">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Triage Priority</span>
          <div className="text-base font-bold text-amber-300 font-sans">
            {state.priority_score.toFixed(4)}
          </div>
          <span className="text-[10px] text-slate-500 block">Queue Weight</span>
        </div>

        {/* Tool Budget Consumed */}
        <div className="p-3 rounded-lg bg-[#071115] border border-[#142a32] space-y-1">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Simulated Tool Cost</span>
          <div className="text-base font-bold text-white font-sans">
            &#8377;{state.total_simulated_tool_cost.toFixed(2)}
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden mt-1">
            <div
              className="bg-cyan-500 h-full rounded-full transition-all"
              style={{ width: `${Math.min(100, (state.total_simulated_tool_cost / state.max_tool_budget) * 100)}%` }}
            />
          </div>
          <span className="text-[9px] text-slate-500 block">&#8377;{state.max_tool_budget.toFixed(2)} max budget</span>
        </div>

        {/* Steps Executed */}
        <div className="p-3 rounded-lg bg-[#071115] border border-[#142a32] space-y-1">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Steps Bounded</span>
          <div className="text-base font-bold text-white font-sans flex items-center gap-1.5">
            <span className="text-cyan-400">{state.step_count}</span>
            <span className="text-xs text-slate-500">/ {state.max_steps} max</span>
          </div>
          <span className="text-[10px] text-emerald-400 block font-mono">
            {Math.round((1 - state.step_count / 9) * 100)}% compressed
          </span>
        </div>
      </div>

      {/* 3. Explicit Stopping Policy Banner */}
      <div className={`p-3.5 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${stoppingBadge.bg}`}>
        <div className="flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <div>
            <div className="font-bold font-sans text-xs uppercase tracking-wide">
              Stopping Trigger: {stoppingBadge.label}
            </div>
            <p className="text-[11px] opacity-90 font-sans mt-0.5">
              {state.stopping_rationale}
            </p>
          </div>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-black/30 border border-white/10 uppercase tracking-wider shrink-0 self-start sm:self-center">
          {state.stopping_status}
        </span>
      </div>

      {/* 4. Ordered Step-by-Step Investigation Trace */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-white uppercase text-[11px] tracking-wider">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>Audit Trace ({state.trace.length} Executed Steps)</span>
          </div>
          <span className="text-[10px] text-slate-500">
            Pre-Execution E[IG] &bull; Real Tool Output &bull; Factual Delta-U
          </span>
        </div>

        {state.trace.length === 0 ? (
          <div className="p-3 rounded-lg bg-[#071115] border border-[#142a32] text-slate-500 text-center italic">
            Zero steps executed. Initial prior uncertainty met stopping condition immediately.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-[#142a32]">
            <table className="w-full text-left text-[11px]">
              <thead className="bg-[#071115] text-slate-400 border-b border-[#142a32] uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2 px-3 font-semibold">Step</th>
                  <th className="py-2 px-3 font-semibold">Tool</th>
                  <th className="py-2 px-3 font-semibold">Pre-E[IG]</th>
                  <th className="py-2 px-3 font-semibold">Cost</th>
                  <th className="py-2 px-3 font-semibold">Uncertainty Delta</th>
                  <th className="py-2 px-3 font-semibold">Output Evidence</th>
                  <th className="py-2 px-3 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#142a32] bg-[#09151b]">
                {state.trace.map((step) => (
                  <tr key={step.step_number} className="hover:bg-[#0d1e26] transition">
                    <td className="py-2.5 px-3 font-bold text-cyan-400">#{step.step_number}</td>
                    <td className="py-2.5 px-3">
                      <span className="font-mono text-white font-semibold">{step.tool_name}</span>
                      <span className="block text-[10px] text-slate-500 font-sans">{step.selection_reason}</span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">
                      {step.expected_information_gain.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">
                      &#8377;{step.simulated_cost.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3">
                      <div className="flex items-center gap-1 font-mono">
                        <span className="text-slate-400">{step.uncertainty_before.toFixed(3)}</span>
                        <ArrowRight className="w-2.5 h-2.5 text-slate-600" />
                        <span className="text-white font-bold">{step.uncertainty_after.toFixed(3)}</span>
                      </div>
                      <span className={`text-[10px] block font-mono ${step.uncertainty_reduction > 0 ? "text-emerald-400" : "text-slate-500"}`}>
                        {step.uncertainty_reduction > 0 ? `-${step.uncertainty_reduction.toFixed(3)}` : "0.000 (no change)"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 max-w-xs">
                      <span className="text-slate-300 font-sans block leading-tight">{step.evidence_summary}</span>
                      {step.evidence_count > 0 && (
                        <span className="text-[10px] text-emerald-400 font-mono">
                          {step.evidence_count} verified record{step.evidence_count > 1 ? "s" : ""}
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${step.tool_status === "SUCCESS" ? "bg-emerald-950 border border-emerald-800 text-emerald-300" : "bg-slate-800 text-slate-400"}`}>
                        {step.tool_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 5. Next Best Action Advisory Decision Support Card */}
      <div className="p-4 rounded-xl bg-[#071115] border-2 border-cyan-900/60 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-[#142a32]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span className="font-bold text-white font-sans text-xs uppercase tracking-wide">
              Advisory Decision Support Recommendation
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-slate-400">Confidence:</span>
            <span className="font-bold text-cyan-300 font-mono">
              {(state.next_best_action.confidence_score * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className={`px-3 py-1.5 rounded-lg border font-bold text-xs tracking-wider uppercase ${getActionBadge(state.next_best_action.recommended_action)}`}>
            {state.next_best_action.recommended_action.replace(/_/g, " ")}
          </div>
          <span className="text-slate-300 text-xs font-sans">
            {state.next_best_action.reason}
          </span>
        </div>

        {/* Policy factors & economic impact */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-[11px] font-sans">
          <div className="space-y-1 bg-[#0b151b] p-2.5 rounded border border-[#142a32]">
            <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block font-mono">
              Key Policy Drivers
            </span>
            <ul className="space-y-0.5 text-slate-300 list-disc list-inside">
              {state.next_best_action.policy_relevant_factors.map((f, idx) => (
                <li key={idx}>{f}</li>
              ))}
            </ul>
          </div>

          <div className="space-y-1 bg-[#0b151b] p-2.5 rounded border border-[#142a32]">
            <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block font-mono">
              Modeled Financial Impact
            </span>
            <p className="text-slate-300 leading-relaxed">
              {state.next_best_action.expected_financial_impact}
            </p>
          </div>
        </div>

        {/* MANDATORY REGULATORY SAFETY BANNER */}
        <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-800/80 flex items-center justify-between text-rose-200">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
            <span className="font-bold font-sans text-xs tracking-wide">
              RECOMMENDATION ONLY &mdash; HUMAN APPROVAL REQUIRED
            </span>
          </div>
          <span className="text-[10px] font-mono text-rose-300 hidden sm:inline">
            Zero Autonomous Financial Action
          </span>
        </div>
      </div>
    </div>
  );
}
