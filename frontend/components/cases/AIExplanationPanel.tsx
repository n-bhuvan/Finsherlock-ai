"use client";

import { useEffect, useState } from "react";
import {
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  FileText,
  HelpCircle,
  Hash,
  Clock,
  Layers,
  Link as LinkIcon,
  Cpu,
  Lock,
} from "lucide-react";
import { LLMExplanationResponse } from "@/types/explanation";
import { getGroundedExplanation, generateGroundedExplanation } from "@/lib/api";

interface AIExplanationPanelProps {
  transactionId: string;
}

export function AIExplanationPanel({ transactionId }: AIExplanationPanelProps) {
  const [data, setData] = useState<LLMExplanationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showClaims, setShowClaims] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getGroundedExplanation(transactionId).then((res) => {
      if (!isMounted) return;
      if (res.data) {
        setData(res.data);
      } else {
        setError(res.error || "Failed to load forensic AI explanation.");
      }
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [transactionId]);

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      const res = await generateGroundedExplanation(transactionId, false);
      if (res.data) {
        setData(res.data);
      }
    } catch (err: any) {
      console.error("Regeneration error:", err);
    } finally {
      setRegenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] font-mono text-xs text-slate-400 animate-pulse flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-cyan-400 animate-spin" />
        Synthesizing evidence-grounded forensic explanation &amp; validating claims...
      </div>
    );
  }

  const isNotGenerated = !data && (!error || error.includes("404") || error.toLowerCase().includes("not found") || error.toLowerCase().includes("please generate"));

  if (isNotGenerated) {
    return (
      <div className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-3 font-mono text-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#142a32]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white tracking-wide uppercase font-sans">
              Evidence-Grounded AI Forensic Explanation
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950/70 border border-cyan-800 text-cyan-300">
              STAGE 16
            </span>
          </div>
          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="px-3 py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-700/60 text-cyan-200 font-bold transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${regenerating ? "animate-spin text-cyan-400" : ""}`} />
            <span>{regenerating ? "Synthesizing Explanation..." : "Generate AI Forensic Explanation"}</span>
          </button>
        </div>
        <p className="text-slate-400 text-xs font-sans">
          No forensic explanation generated yet for this transaction. In accordance with strict GET semantics, explanations are generated on-demand via POST with full cryptographic audit trail logging.
        </p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-rose-900/50 text-rose-300 font-mono text-xs space-y-2">
        <div className="flex items-center gap-2 font-bold">
          <AlertTriangle className="w-4 h-4 text-rose-400" />
          Forensic AI Explanation Unavailable
        </div>
        <p>{error}</p>
        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="px-2.5 py-1 rounded bg-rose-950 border border-rose-800 text-rose-200 text-[10px] font-bold"
        >
          {regenerating ? "Retrying..." : "Retry Generation"}
        </button>
      </div>
    );
  }

  if (!data) return null;

  const isFullyGrounded = data.grounding_validation.is_fully_grounded;
  const groundingPct = (data.grounding_validation.grounding_ratio * 100).toFixed(1);

  return (
    <div className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-5 font-mono text-xs">
      {/* 1. Header with Grounding Badge & Immutability */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#142a32]">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white tracking-wide uppercase font-sans">
              Evidence-Grounded AI Forensic Explanation
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950/70 border border-cyan-800 text-cyan-300">
              STAGE 16
            </span>
          </div>
          <p className="text-slate-400 text-[11px] font-sans">
            Provider: <code className="text-cyan-300">{data.metadata.provider}</code> ({data.metadata.model}) &bull; Prompt Version: <code className="text-slate-300">{data.metadata.prompt_version}</code>
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Grounding Badge */}
          <div className={`px-2.5 py-1 rounded border text-[10px] font-bold flex items-center gap-1.5 ${
            isFullyGrounded
              ? "bg-emerald-950/60 border-emerald-800 text-emerald-300"
              : "bg-amber-950/60 border-amber-800 text-amber-300"
          }`}>
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>{isFullyGrounded ? "100% Grounded in Verified Evidence" : `${groundingPct}% Grounded Claims`}</span>
          </div>

          {/* Fallback Badge if active */}
          {data.metadata.is_fallback && (
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 border border-slate-700 text-slate-300">
              Deterministic Fallback
            </span>
          )}

          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="px-2.5 py-1 rounded bg-[#071115] hover:bg-[#0e212a] border border-[#142a32] text-slate-300 hover:text-white transition flex items-center gap-1.5 cursor-pointer text-[11px]"
          >
            <RotateCcw className={`w-3 h-3 ${regenerating ? "animate-spin text-cyan-400" : ""}`} />
            <span>{regenerating ? "Validating..." : "Refresh"}</span>
          </button>
        </div>
      </div>

      {/* 2. Immutable Risk Scores Banner (Direct Backend Lock) */}
      <div className="p-3 rounded-lg bg-[#071115] border border-[#142a32] flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Lock className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">
            Immutable Model Risk Priors (Locked Against LLM Alteration):
          </span>
        </div>
        <div className="flex items-center gap-4 text-[11px]">
          <div>
            <span className="text-slate-500">Model A: </span>
            <span className="text-white font-bold">{(data.model_a_probability * 100).toFixed(2)}%</span>
          </div>
          <div>
            <span className="text-slate-500">Model B: </span>
            <span className="text-white font-bold">{(data.model_b_probability * 100).toFixed(2)}%</span>
          </div>
          <div>
            <span className="text-slate-500">Platt Calibrated: </span>
            <span className="text-cyan-300 font-bold">{(data.calibrated_risk * 100).toFixed(2)}%</span>
          </div>
          <div>
            <span className="text-slate-500">Band: </span>
            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
              data.risk_band === "CRITICAL" || data.risk_band === "HIGH" ? "bg-rose-950 text-rose-300 border border-rose-800" : "bg-emerald-950 text-emerald-300 border border-emerald-800"
            }`}>
              {data.risk_band}
            </span>
          </div>
        </div>
      </div>

      {/* 3. Executive Summary Brief */}
      <div className="space-y-1.5 p-3.5 rounded-lg bg-[#071115] border border-[#142a32]">
        <div className="flex items-center gap-2 text-white font-bold text-xs uppercase tracking-wide font-sans">
          <FileText className="w-3.5 h-3.5 text-cyan-400" />
          <span>Forensic Executive Summary</span>
        </div>
        <p className="text-slate-300 leading-relaxed font-sans text-xs">
          {data.executive_summary}
        </p>
      </div>

      {/* 4. Risk Assessment & Topological Interpretation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-sans text-xs">
        <div className="p-3 rounded-lg bg-[#071115] border border-[#142a32] space-y-1.5">
          <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block font-mono">
            Model Risk Context Narrative
          </span>
          <p className="text-slate-300 leading-relaxed">
            {data.risk_assessment_narrative}
          </p>
        </div>

        <div className="p-3 rounded-lg bg-[#071115] border border-[#142a32] space-y-1.5">
          <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block font-mono">
            Topological Graph Interpretation
          </span>
          <p className="text-slate-300 leading-relaxed">
            {data.topological_ring_interpretation}
          </p>
        </div>
      </div>

      {/* 5. Structured Claim-Level Verification Table */}
      <div className="space-y-2">
        <div className="flex items-center justify-between cursor-pointer" onClick={() => setShowClaims(!showClaims)}>
          <div className="flex items-center gap-2">
            <span className="font-bold text-white uppercase text-[11px] tracking-wider">
              Structured Claim Verification ({data.structured_claims.length} Claims)
            </span>
            <span className="text-[10px] text-slate-500">
              ({data.grounding_validation.grounded_fact_claims}/{data.grounding_validation.total_fact_claims} FACT claims mapped)
            </span>
          </div>
          <span className="text-[10px] text-cyan-400 hover:underline">
            {showClaims ? "Hide Claims" : "Show Claims"}
          </span>
        </div>

        {showClaims && (
          <div className="overflow-x-auto rounded-lg border border-[#142a32]">
            <table className="w-full text-left text-[11px]">
              <thead className="bg-[#071115] text-slate-400 border-b border-[#142a32] uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2 px-3 font-semibold w-20">Claim ID</th>
                  <th className="py-2 px-3 font-semibold w-24">Type</th>
                  <th className="py-2 px-3 font-semibold">Assertion Statement</th>
                  <th className="py-2 px-3 font-semibold w-28 text-center">Citations</th>
                  <th className="py-2 px-3 font-semibold w-24 text-right">Grounding</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#142a32] bg-[#09151b]">
                {data.structured_claims.map((c, idx) => (
                  <tr key={idx} className="hover:bg-[#0d1e26] transition">
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-300">{c.claim_id}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                        c.claim_type === "FACT" ? "bg-cyan-950 text-cyan-300 border border-cyan-800" :
                        c.claim_type === "INTERPRETATION" ? "bg-purple-950 text-purple-300 border border-purple-800" :
                        "bg-slate-800 text-slate-400"
                      }`}>
                        {c.claim_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-200 font-sans">{c.statement}</td>
                    <td className="py-2.5 px-3 text-center font-mono">
                      {c.evidence_ids.length > 0 ? (
                        <div className="flex flex-wrap gap-1 justify-center">
                          {c.evidence_ids.map((eid, eidx) => (
                            <span key={eidx} className="px-1 py-0.5 rounded bg-[#071115] border border-[#142a32] text-[9px] text-cyan-300">
                              {eid}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-600 text-[10px]">&mdash;</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold">
                      {c.is_grounded ? (
                        <span className="text-emerald-400 text-[10px] flex items-center gap-1 justify-end">
                          <CheckCircle2 className="w-3 h-3" /> VERIFIED
                        </span>
                      ) : (
                        <span className="text-rose-400 text-[10px] flex items-center gap-1 justify-end">
                          <AlertTriangle className="w-3 h-3" /> REJECTED
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 6. Benign Hypotheses & Human Verification Questions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-sans">
        {/* Benign Alternative Hypotheses */}
        <div className="p-3.5 rounded-lg bg-[#071115] border border-[#142a32] space-y-2">
          <div className="flex items-center gap-2 text-white font-bold text-xs uppercase font-mono">
            <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
            <span>Plausible Benign Hypotheses</span>
          </div>
          <div className="space-y-2">
            {data.benign_alternative_hypotheses.map((h, idx) => (
              <div key={idx} className="p-2 rounded bg-[#0b151b] border border-[#142a32] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-[11px]">{h.title}</span>
                  <span className="text-[9px] font-mono text-cyan-300 bg-[#071115] px-1 py-0.5 rounded border border-[#142a32]">
                    {h.triggering_evidence_id}
                  </span>
                </div>
                <p className="text-slate-300 text-[11px] leading-relaxed">{h.rationale}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recommended Human Verification Questions */}
        <div className="p-3.5 rounded-lg bg-[#071115] border border-[#142a32] space-y-2">
          <div className="flex items-center gap-2 text-white font-bold text-xs uppercase font-mono">
            <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Recommended Human Verification Checklist</span>
          </div>
          <ul className="space-y-1.5 text-slate-300 text-[11px] list-disc list-inside leading-relaxed">
            {data.recommended_human_verification_questions.map((q, idx) => (
              <li key={idx} className="pl-1">{q}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* 7. Hash-Chained Audit Trail Metadata */}
      <div className="p-3 rounded-lg bg-[#071115] border border-[#142a32] space-y-1 text-[10px] text-slate-400 font-mono">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <span className="text-slate-300 font-bold flex items-center gap-1.5">
            <Hash className="w-3 h-3 text-cyan-400" />
            Audit ID: <code className="text-cyan-300">{data.audit_id}</code>
          </span>
          <span>Latency: {data.metadata.latency_ms.toFixed(1)}ms</span>
        </div>
        <div className="flex items-center justify-between flex-wrap gap-2 pt-1 border-t border-[#142a32]/60 text-[9px]">
          <span className="truncate max-w-xs">Prompt SHA: {data.metadata.prompt_sha256.slice(0, 16)}...</span>
          <span className="truncate max-w-xs">Response SHA: {data.metadata.response_sha256.slice(0, 16)}...</span>
          <span className="text-emerald-400 font-bold">Hash-Chained Log Appended</span>
        </div>
      </div>

      {/* 8. MANDATORY REGULATORY SAFETY BANNER */}
      <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-800/80 flex items-center justify-between text-rose-200">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
          <span className="font-bold font-sans text-xs tracking-wide">
            DECISION SUPPORT EXPLANATION &mdash; MANDATORY HUMAN APPROVAL REQUIRED
          </span>
        </div>
        <span className="text-[10px] font-mono text-rose-300 hidden sm:inline">
          Zero Autonomous Action Permitted
        </span>
      </div>
    </div>
  );
}
