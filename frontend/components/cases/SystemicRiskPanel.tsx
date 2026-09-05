"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Server,
  Share2,
  Shield,
  ShieldAlert,
  Store,
  User,
} from "lucide-react";
import { SystemicAnomalyResponse, ScopeAnomalyResult, AnomalyScope } from "@/types/anomaly";
import { getSystemicAnomaly } from "@/lib/api";

interface SystemicRiskPanelProps {
  transactionId: string;
}

export function SystemicRiskPanel({ transactionId }: SystemicRiskPanelProps) {
  const [data, setData] = useState<SystemicAnomalyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getSystemicAnomaly(transactionId).then((res) => {
      if (!isMounted) return;
      if (res.data) {
        setData(res.data);
      } else {
        setError(res.error || "Failed to evaluate systemic anomaly.");
      }
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [transactionId]);

  if (loading) {
    return (
      <div className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] text-slate-400 font-mono text-xs flex items-center gap-3 animate-pulse">
        <Activity className="w-4 h-4 text-cyan-400 animate-spin" />
        <span>Evaluating deterministic systemic anomaly signals across 4 scopes...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-rose-900/30 text-rose-300 font-mono text-xs flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
        <span>Systemic Anomaly: {error || "Unavailable"}</span>
      </div>
    );
  }

  const getScopeIcon = (scope: AnomalyScope) => {
    switch (scope) {
      case "ACCOUNT":
        return <User className="w-4 h-4 text-cyan-400" />;
      case "MERCHANT":
        return <Store className="w-4 h-4 text-purple-400" />;
      case "RING_NETWORK":
        return <Share2 className="w-4 h-4 text-rose-400" />;
      case "SYSTEMIC_INFRASTRUCTURE":
        return <Server className="w-4 h-4 text-amber-400" />;
    }
  };

  const getScopeTitle = (scope: AnomalyScope) => {
    switch (scope) {
      case "ACCOUNT":
        return "Account / Customer Anomaly";
      case "MERCHANT":
        return "Merchant Recipient Anomaly";
      case "RING_NETWORK":
        return "Ring / Network Anomaly";
      case "SYSTEMIC_INFRASTRUCTURE":
        return "Possible Systemic / Infrastructure";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "ANOMALOUS":
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-rose-950/70 border border-rose-500/40 text-rose-300 flex items-center gap-1">
            <ShieldAlert className="w-3 h-3 text-rose-400" />
            ANOMALOUS
          </span>
        );
      case "NORMAL":
        return (
          <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            NORMAL
          </span>
        );
      case "NOT_APPLICABLE":
        return (
          <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-slate-900 border border-slate-700 text-slate-400 flex items-center gap-1">
            <HelpCircle className="w-3 h-3 text-slate-500" />
            NOT APPLICABLE
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-amber-950/60 border border-amber-500/30 text-amber-300">
            {status}
          </span>
        );
    }
  };

  const scopeList: ScopeAnomalyResult[] = [
    data.scopes.account,
    data.scopes.merchant,
    data.scopes.ring_network,
    data.scopes.systemic_infrastructure,
  ];

  return (
    <div className="rounded-xl bg-[#0b151b] border border-[#142a32] overflow-hidden shadow-xl">
      {/* Header Banner */}
      <div className="p-4 sm:p-5 border-b border-[#142a32] bg-[#071015]/60 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <Activity className="w-5 h-5 text-cyan-400" />
            <h3 className="font-semibold text-white text-base">
              Systemic Risk Anomaly Detection
            </h3>
            <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-cyan-950 border border-cyan-500/40 text-cyan-300">
              V2 Stage 15
            </span>
            <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-900 border border-slate-700 text-slate-400">
              Deterministic Anomaly Heuristic
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Multi-scope empirical anomaly layer differentiating account, merchant, ring network,
            and shared infrastructure correlation. Evaluated strictly on point-in-time observational data.
          </p>
        </div>

        {/* Global Anomaly Score Callout */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="text-right">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">
              Systemic Anomaly Score
            </div>
            <div
              className={`text-xl font-mono font-bold ${
                data.systemic_anomaly_score >= 0.6
                  ? "text-rose-400"
                  : data.systemic_anomaly_score >= 0.3
                  ? "text-amber-400"
                  : "text-emerald-400"
              }`}
            >
              {(data.systemic_anomaly_score * 100).toFixed(1)}%
            </div>
          </div>
          <div className="pl-3 border-l border-[#142a32]">
            {data.anomaly_detected ? (
              <span className="px-2.5 py-1 text-xs font-bold rounded bg-rose-950/80 border border-rose-500/50 text-rose-300 flex items-center gap-1.5 shadow-sm">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                ANOMALY DETECTED
              </span>
            ) : (
              <span className="px-2.5 py-1 text-xs font-bold rounded bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                NOMINAL PROFILE
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 4-Scope Cards Grid */}
      <div className="p-4 sm:p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
        {scopeList.map((sc) => {
          const isAnomalous = sc.status === "ANOMALOUS";
          const isNotApplicable = sc.status === "NOT_APPLICABLE";

          return (
            <div
              key={sc.scope}
              className={`p-4 rounded-lg border transition-all flex flex-col justify-between ${
                isAnomalous
                  ? "bg-rose-950/15 border-rose-900/40"
                  : isNotApplicable
                  ? "bg-[#071015]/40 border-slate-800/60"
                  : "bg-[#071015]/70 border-[#142a32]"
              }`}
            >
              <div>
                {/* Scope Header */}
                <div className="flex items-center justify-between gap-2 mb-2.5">
                  <div className="flex items-center gap-2">
                    {getScopeIcon(sc.scope)}
                    <span className="text-xs font-semibold text-slate-200">
                      {getScopeTitle(sc.scope)}
                    </span>
                  </div>
                  {getStatusBadge(sc.status)}
                </div>

                {/* Score & Justification */}
                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-[11px] text-slate-400">Scope Score</span>
                  <span
                    className={`font-mono text-xs font-bold ${
                      isAnomalous
                        ? "text-rose-400"
                        : isNotApplicable
                        ? "text-slate-500"
                        : "text-emerald-400"
                    }`}
                  >
                    {isNotApplicable ? "N/A" : `${(sc.anomaly_score * 100).toFixed(1)}%`}
                  </span>
                </div>

                <p className="text-[11px] text-slate-300 leading-relaxed bg-[#0b151b]/80 p-2 rounded border border-[#142a32]/60 mb-3">
                  {sc.reason}
                </p>

                {/* Evaluated Empirical Signals */}
                {sc.signals.length > 0 && (
                  <div className="space-y-1.5 mb-3">
                    <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400">
                      Empirical Signals
                    </div>
                    {sc.signals.map((sig) => (
                      <div
                        key={sig.name}
                        className="text-[10px] font-mono flex items-start justify-between gap-2 p-1.5 rounded bg-black/20 border border-slate-800/40"
                      >
                        <div className="flex-1">
                          <span className="text-slate-300 block">{sig.description}</span>
                          {sig.source_field && (
                            <span className="text-slate-400 text-[9px]">
                              source: {sig.source_field}
                            </span>
                          )}
                        </div>
                        <span
                          className={`shrink-0 px-1.5 py-0.5 rounded text-[9px] font-bold ${
                            sig.status === "UNAVAILABLE"
                              ? "bg-slate-800 text-slate-400"
                              : sig.is_anomalous
                              ? "bg-rose-950 text-rose-300 border border-rose-700/50"
                              : "bg-emerald-950 text-emerald-300 border border-emerald-700/30"
                          }`}
                        >
                          {sig.status === "UNAVAILABLE"
                            ? "UNAVAILABLE"
                            : sig.is_anomalous
                            ? "ANOMALOUS"
                            : "NORMAL"}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Linked Evidence Badges & Verification Tag */}
              <div className="pt-2 border-t border-[#142a32]/60 flex items-center justify-between text-[10px] text-slate-400">
                <div className="flex items-center gap-1.5 flex-wrap">
                  {sc.evidence_ids.length > 0 ? (
                    sc.evidence_ids.slice(0, 2).map((eid) => (
                      <span
                        key={eid}
                        className="px-1.5 py-0.5 rounded bg-cyan-950/40 border border-cyan-800/40 text-cyan-300 font-mono text-[9px]"
                      >
                        {eid}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-400 text-[9px]">No direct evidence IDs</span>
                  )}
                  {sc.evidence_ids.length > 2 && (
                    <span className="text-slate-400 text-[9px]">
                      +{sc.evidence_ids.length - 2} more
                    </span>
                  )}
                </div>

                {sc.requires_verification && (
                  <span className="text-amber-400/90 text-[10px] font-semibold flex items-center gap-1">
                    <Shield className="w-3 h-3 text-amber-400" />
                    Verify
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Safety & Non-Causal Attribution Disclaimer */}
      <div className="p-3.5 bg-[#071015] border-t border-[#142a32] flex items-start gap-2.5 text-[11px] text-slate-400">
        <Shield className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div className="flex-1">
          <span className="font-semibold text-slate-300">Defense-Only Governance & Safety Rule: </span>
          <span>{data.defense_only_disclaimer}</span>
        </div>
      </div>
    </div>
  );
}
