"use client";

import { useState, useEffect } from "react";
import {
  Network,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Shield,
  Layers,
  Info,
  ShieldAlert,
  UserCheck,
} from "lucide-react";
import { ColdStartResponse } from "@/types/analytics";

export function ColdStartPanel() {
  const [data, setData] = useState<ColdStartResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewScope, setViewScope] = useState<"held_out" | "full">("held_out");

  useEffect(() => {
    async function fetchColdStartData() {
      try {
        const res = await fetch("http://localhost:8000/api/analytics/cold-start");
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
    fetchColdStartData();
  }, []);

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] text-slate-400 font-mono text-xs flex items-center gap-2">
        <div className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        Loading Cold-Start Segmentation Analysis...
      </div>
    );
  }

  if (!data || data.status === "Unavailable" || !data.rule_sufficiency_audit) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] text-slate-400 font-mono text-xs space-y-2">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <AlertTriangle className="w-4 h-4" />
          <span>Cold-Start Segmentation Benchmark Unavailable</span>
        </div>
        <p className="text-[11px] text-slate-500">
          Cold-start evaluation artifacts not loaded. Run <code className="text-cyan-300">python scripts/run_stage14_evaluation.py</code> to generate benchmark data.
        </p>
      </div>
    );
  }

  const evalScope = viewScope === "held_out" ? data.held_out_test_evaluation! : data.full_dataset_evaluation!;
  const dist = evalScope.confidence_distribution;
  const slices = evalScope.slices;
  const total = evalScope.total_samples;

  return (
    <div className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-[#142a32] pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Network className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white font-sans tracking-wide">
              Cold-Start Segmentation &amp; Graph Confidence (Stage 14)
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950/80 border border-cyan-700/60 text-cyan-300">
              Zero Model B Input Mutation
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans">
            Point-in-time graph confidence precedence hierarchy. Evaluates Model A and Model B performance across separate Cold-Start vs Mature transaction slices.
          </p>
        </div>

        {/* Scope Selector */}
        <div className="flex items-center gap-2 bg-[#081216] p-1 rounded-lg border border-[#142a32]">
          <button
            onClick={() => setViewScope("held_out")}
            className={`px-3 py-1 rounded text-[11px] transition-all ${
              viewScope === "held_out"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Held-Out Test (N=300)
          </button>
          <button
            onClick={() => setViewScope("full")}
            className={`px-3 py-1 rounded text-[11px] transition-all ${
              viewScope === "full"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Full Dataset (N=2,000)
          </button>
        </div>
      </div>

      {/* Graph Confidence Precedence Distribution Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* UNAVAILABLE */}
        <div className="p-3.5 rounded-xl bg-[#081216] border border-amber-500/30 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
              1. UNAVAILABLE
            </span>
            <span className="text-[10px] font-mono text-slate-400">
              {((dist.UNAVAILABLE / total) * 100).toFixed(1)}%
            </span>
          </div>
          <div className="text-xl font-bold text-white font-sans">
            {dist.UNAVAILABLE.toLocaleString()} <span className="text-xs text-slate-400 font-normal">transactions</span>
          </div>
          <p className="text-[10px] text-slate-400 font-sans leading-relaxed">
            Completely isolated at transaction time (connected accounts = 0). Graph signals are ungrounded.
          </p>
        </div>

        {/* LIMITED */}
        <div className="p-3.5 rounded-xl bg-[#081216] border border-cyan-500/30 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">
              2. LIMITED
            </span>
            <span className="text-[10px] font-mono text-slate-400">
              {((dist.LIMITED / total) * 100).toFixed(1)}%
            </span>
          </div>
          <div className="text-xl font-bold text-white font-sans">
            {dist.LIMITED.toLocaleString()} <span className="text-xs text-slate-400 font-normal">transactions</span>
          </div>
          <p className="text-[10px] text-slate-400 font-sans leading-relaxed">
            Early behavioral infancy (first transaction observed or ≤ 2 historical transactions).
          </p>
        </div>

        {/* VERIFIED */}
        <div className="p-3.5 rounded-xl bg-[#081216] border border-emerald-500/30 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
              3. VERIFIED
            </span>
            <span className="text-[10px] font-mono text-slate-400">
              {((dist.VERIFIED / total) * 100).toFixed(1)}%
            </span>
          </div>
          <div className="text-xl font-bold text-white font-sans">
            {dist.VERIFIED.toLocaleString()} <span className="text-xs text-slate-400 font-normal">transactions</span>
          </div>
          <p className="text-[10px] text-slate-400 font-sans leading-relaxed">
            Established multi-transaction behavioral history and graph topologies.
          </p>
        </div>
      </div>

      {/* Candidate Rule Audit Table */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-xs font-bold text-white font-sans">
              Candidate Cold-Start Rule Sufficiency Audit (Full Dataset N=2,000)
            </span>
          </div>
          <span className="text-[10px] text-slate-500">Threshold: N &ge; 20 Required for Slice Statistical Sufficiency</span>
        </div>

        <div className="overflow-x-auto rounded-lg border border-[#142a32]">
          <table className="w-full text-left bg-[#081216]">
            <thead>
              <tr className="text-[10px] text-slate-400 border-b border-[#142a32] bg-[#0b151b]">
                <th className="py-2 px-2">Rule ID</th>
                <th className="py-2 px-2">Rule Name &amp; Condition</th>
                <th className="py-2 px-2 text-right">Sample (N)</th>
                <th className="py-2 px-2 text-right">Pos / Neg</th>
                <th className="py-2 px-2 text-center">Sufficiency Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#142a32]/60 text-[11px]">
              {data.rule_sufficiency_audit?.map((r) => {
                const isInsufficient = r.sufficiency === "INSUFFICIENT";
                return (
                  <tr key={r.rule_id} className="hover:bg-[#0b151b]/60">
                    <td className="py-2 px-2 font-mono text-cyan-300 font-semibold">{r.rule_id}</td>
                    <td className="py-2 px-2">
                      <div className="font-semibold text-slate-200">{r.rule_name}</div>
                      <div className="text-[10px] text-slate-400 font-sans">{r.description}</div>
                    </td>
                    <td className="py-2 px-2 text-right font-mono font-bold text-white">{r.sample_count}</td>
                    <td className="py-2 px-2 text-right font-mono text-slate-400">
                      {r.positive_count} / {r.negative_count}
                    </td>
                    <td className="py-2 px-2 text-center">
                      {isInsufficient ? (
                        <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-amber-950/80 text-amber-300 border border-amber-700/60 uppercase">
                          {r.status}
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 uppercase">
                          {r.status}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slices Performance Table: Model A vs Model B */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-xs font-bold text-white font-sans">
              Performance Slices Across Confidence Segments (Threshold T=0.70)
            </span>
          </div>
          <span className="text-[10px] text-slate-500">Zero Model Input Modification</span>
        </div>

        <div className="overflow-x-auto rounded-lg border border-[#142a32]">
          <table className="w-full text-left bg-[#081216]">
            <thead>
              <tr className="text-[10px] text-slate-400 border-b border-[#142a32] bg-[#0b151b]">
                <th className="py-2 px-2">Segment Slice</th>
                <th className="py-2 px-2 text-right">Samples (Pos / Neg)</th>
                <th className="py-2 px-2 text-right">Model A F1</th>
                <th className="py-2 px-2 text-right">Model B F1</th>
                <th className="py-2 px-2 text-right">Model A Recall</th>
                <th className="py-2 px-2 text-right">Model B Recall</th>
                <th className="py-2 px-2 text-right">FPR Delta</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#142a32]/60 text-[11px]">
              {Object.entries(slices).map(([sliceKey, s]) => {
                return (
                  <tr key={sliceKey} className="hover:bg-[#0b151b]/60">
                    <td className="py-2 px-2 font-semibold text-white capitalize font-sans">
                      {sliceKey.replace("_", " ")}
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-slate-300">
                      {s.sample_count} ({s.positive_count} / {s.negative_count})
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-slate-300">
                      {s.model_a.f1.toFixed(4)}
                    </td>
                    <td className="py-2 px-2 text-right font-mono font-bold text-cyan-300">
                      {s.model_b.f1.toFixed(4)}
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-slate-300">
                      {s.model_a.recall.toFixed(4)}
                    </td>
                    <td className="py-2 px-2 text-right font-mono font-bold text-emerald-300">
                      {s.model_b.recall.toFixed(4)}
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-[10px]">
                      {s.deltas.fpr_delta === 0 ? (
                        <span className="text-slate-400">0.0000</span>
                      ) : (
                        <span className={s.deltas.fpr_delta < 0 ? "text-emerald-400" : "text-amber-400"}>
                          {s.deltas.fpr_delta > 0 ? `+${s.deltas.fpr_delta.toFixed(4)}` : s.deltas.fpr_delta.toFixed(4)}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Advisory Policy & Safety Guardrail Banner */}
      <div className="p-3.5 rounded-lg bg-[#08161d] border border-cyan-500/30 text-[10px] text-slate-300 font-sans space-y-1.5">
        <div className="flex items-center gap-1.5 font-bold text-cyan-300">
          <UserCheck className="w-3.5 h-3.5" />
          <span>Cold-Start Decision Support Policy &amp; Safety Guardrails</span>
        </div>
        <p className="leading-relaxed text-slate-400">
          {data.metadata?.advisory_policy ??
            "Decision-Support Policy: When graph_confidence is LIMITED or UNAVAILABLE, investigators are advised to prioritize transactional and behavioral signals, request Tier-1 identity verification, and perform manual verification before taking action. Automated blocking is never performed autonomously."}
        </p>
        <p className="leading-relaxed text-slate-500 italic">
          Safety Guarantee: Model B 58-feature inputs were strictly preserved without feature alteration or synthetic empirical imputation.
        </p>
      </div>
    </div>
  );
}
