"use client";

import React, { useEffect, useState } from "react";
import { getPolicyDecision } from "@/lib/api";
import { PolicyDecision, PolicyAction } from "@/types/policy";
import {
  ShieldAlert,
  ShieldCheck,
  Eye,
  UserCheck,
  AlertTriangle,
  HelpCircle,
  Clock,
  Lock,
  CheckCircle2,
  FileSearch,
  Layers,
} from "lucide-react";

interface PolicyDecisionCardProps {
  transactionId: string;
}

export function PolicyDecisionCard({ transactionId }: PolicyDecisionCardProps) {
  const [decision, setDecision] = useState<PolicyDecision | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getPolicyDecision(transactionId)
      .then((res) => {
        if (!isMounted) return;
        if (res.data) {
          setDecision(res.data);
        } else {
          setError(res.error || "Unable to retrieve policy decision.");
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || "Failed to load policy decision.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [transactionId]);

  if (loading) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-md animate-pulse">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-8 h-8 bg-slate-800 rounded-lg"></div>
          <div className="h-6 w-64 bg-slate-800 rounded"></div>
        </div>
        <div className="h-24 bg-slate-800/40 rounded-lg mb-4"></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="h-16 bg-slate-800/40 rounded-lg"></div>
          <div className="h-16 bg-slate-800/40 rounded-lg"></div>
          <div className="h-16 bg-slate-800/40 rounded-lg"></div>
          <div className="h-16 bg-slate-800/40 rounded-lg"></div>
        </div>
      </div>
    );
  }

  if (error || !decision) {
    return (
      <div className="bg-slate-900/60 border border-red-900/40 rounded-xl p-6 shadow-xl text-slate-300">
        <div className="flex items-center space-x-3 text-red-400 font-semibold mb-2">
          <AlertTriangle className="w-5 h-5" />
          <span>Policy Engine Status: Offline or Degraded</span>
        </div>
        <p className="text-sm text-slate-400">{error || "No policy decision available for this transaction."}</p>
      </div>
    );
  }

  const getActionBadge = (action: PolicyAction) => {
    switch (action) {
      case "ESCALATE":
        return {
          bg: "bg-red-950/70 border-red-700 text-red-300",
          icon: ShieldAlert,
          label: "ESCALATE",
          disclaimer: "Escalation recommendation -- no autonomous enforcement executed.",
          color: "text-red-400",
        };
      case "HOLD_FOR_REVIEW":
        return {
          bg: "bg-amber-950/70 border-amber-700 text-amber-300",
          icon: Clock,
          label: "HOLD FOR REVIEW",
          disclaimer: "Human review queue recommendation -- no transaction hold executed.",
          color: "text-amber-400",
        };
      case "REQUEST_VERIFICATION":
        return {
          bg: "bg-purple-950/70 border-purple-700 text-purple-300",
          icon: UserCheck,
          label: "REQUEST VERIFICATION",
          disclaimer: "Verification recommendation -- no automated customer contact executed.",
          color: "text-purple-400",
        };
      case "MONITOR":
        return {
          bg: "bg-blue-950/70 border-blue-700 text-blue-300",
          icon: Eye,
          label: "MONITOR",
          disclaimer: "Telemetry observation recommendation -- no automated account action executed.",
          color: "text-blue-400",
        };
      case "ALLOW":
        return {
          bg: "bg-emerald-950/70 border-emerald-700 text-emerald-300",
          icon: ShieldCheck,
          label: "ALLOW",
          disclaimer: "Analytical recommendation only -- no payment approval executed.",
          color: "text-emerald-400",
        };
      case "FALLBACK_REVIEW":
      default:
        return {
          bg: "bg-slate-800/80 border-slate-600 text-slate-300",
          icon: HelpCircle,
          label: "FALLBACK REVIEW",
          disclaimer: "Manual review required due to unavailable signals.",
          color: "text-slate-400",
        };
    }
  };

  const badge = getActionBadge(decision.recommended_action);
  const ActionIcon = badge.icon;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-2xl backdrop-blur-md space-y-6">
      {/* Header with Title and Strict Safety Boundaries */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-bold text-slate-100 tracking-tight">
                Deterministic Risk Policy Engine
              </h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
                {decision.policy_version}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Stage 19 -- Next-Best-Action Human Decision Support Layer
            </p>
          </div>
        </div>

        {/* Triple Defense Safety Flags */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-emerald-950/50 border border-emerald-800/60 text-emerald-400 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>HUMAN APPROVAL REQUIRED</span>
          </div>
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700 text-slate-300 font-medium">
            <Lock className="w-3.5 h-3.5" />
            <span>NOT EXECUTED</span>
          </div>
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700 text-slate-300 font-medium">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>NO AUTONOMOUS ACTION</span>
          </div>
        </div>
      </div>

      {/* Prominent Next-Best-Action Recommendation Banner */}
      <div className={`p-5 rounded-xl border ${badge.bg} transition-all`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-xs font-semibold tracking-wider uppercase text-slate-400">
              NEXT-BEST-ACTION (RECOMMENDATION ONLY)
            </span>
            <div className="flex items-center space-x-3">
              <ActionIcon className={`w-8 h-8 ${badge.color}`} />
              <div>
                <h2 className="text-2xl font-black tracking-wide text-white">
                  {badge.label}
                </h2>
                <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
                  <span>Priority: {decision.action_priority}</span>
                  <span>*</span>
                  <span>Rule: {decision.policy_rule_id}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action-Specific Mandatory Regulatory Disclaimer */}
          <div className="max-w-md p-3 rounded-lg bg-black/40 border border-white/10 text-xs text-slate-300">
            <p className="font-medium text-slate-200">Governance Notice:</p>
            <p className="italic text-slate-400 mt-0.5">{decision.disclaimer}</p>
          </div>
        </div>
      </div>

      {/* Why this Action? Explanation Rationale */}
      <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
          <FileSearch className="w-4 h-4 text-indigo-400" />
          <span>Why this action?</span>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed font-sans">
          {decision.policy_reason}
        </p>
      </div>

      {/* Multi-Stage Decision Signals Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-center">
        <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800">
          <div className="text-xs text-slate-400">Calibrated Risk</div>
          <div className="text-base font-bold text-slate-100 mt-1 font-mono">
            {(decision.calibrated_risk_score * 100).toFixed(1)}%
          </div>
          <div className="text-[10px] text-slate-400">Model B Platt</div>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800">
          <div className="text-xs text-slate-400">Expected Value</div>
          <div className={`text-base font-bold mt-1 font-mono ${decision.expected_value >= 0 ? "text-emerald-400" : "text-slate-400"}`}>
            INR {decision.expected_value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
          </div>
          <div className="text-[10px] text-slate-400">Net Saved Triage</div>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800">
          <div className="text-xs text-slate-400">Priority Score</div>
          <div className="text-base font-bold text-slate-100 mt-1 font-mono">
            {decision.priority_score.toFixed(3)}
          </div>
          <div className="text-[10px] text-slate-400">Portfolio Rank</div>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800">
          <div className="text-xs text-slate-400">Uncertainty</div>
          <div className="text-base font-bold text-slate-100 mt-1 font-mono">
            {decision.investigative_uncertainty.toFixed(4)}
          </div>
          <div className="text-[10px] text-slate-400">
            {decision.investigative_uncertainty <= 0.12 ? "Resolved (<=0.12)" : decision.investigative_uncertainty > 0.40 ? "Elevated (>0.40)" : "Acceptable"}
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800">
          <div className="text-xs text-slate-400">Systemic Anomaly</div>
          <div className="text-base font-bold text-slate-100 mt-1 font-mono">
            {decision.systemic_anomaly_score.toFixed(4)}
          </div>
          <div className="text-[10px] text-slate-400">Multi-Scope Stage 15</div>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800">
          <div className="text-xs text-slate-400">Evidence Domains</div>
          <div className="text-base font-bold text-slate-100 mt-1 font-mono">
            {decision.corroborated_structural_domains}
          </div>
          <div className="text-[10px] text-slate-400">
            {decision.evidence_domains.length > 0 ? decision.evidence_domains.join(", ") : "None Verified"}
          </div>
        </div>
      </div>

      {/* Human Role & Required Forensic Verification */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-800/80">
        <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
            Assigned Human Review Role
          </div>
          <div className="text-sm font-bold text-indigo-400 font-mono">
            {decision.required_human_role}
          </div>
          <p className="text-xs text-slate-400">
            Designated risk personnel tier authorized to conduct triage and verify factual records.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-1">
          <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
            Required Forensic Verification
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            {decision.required_verification}
          </p>
        </div>
      </div>

      {/* Counterfactual Insight summary if available */}
      {decision.counterfactual_context && (
        <div className="text-xs text-slate-400 flex items-center justify-between p-3 rounded-lg bg-slate-950/40 border border-slate-800/60">
          <span>
            Model Sensitivity Driver:{" "}
            <span className="font-mono text-slate-200">
              {decision.counterfactual_context.strongest_driver}
            </span>{" "}
            ({decision.counterfactual_context.driver_direction})
          </span>
          {decision.counterfactual_context.largest_reduction_delta !== undefined && (
            <span>
              Max What-If Risk Delta:{" "}
              <span className="font-mono text-emerald-400 font-semibold">
                {decision.counterfactual_context.largest_reduction_delta.toFixed(4)}
              </span>
            </span>
          )}
        </div>
      )}
    </div>
  );
}
