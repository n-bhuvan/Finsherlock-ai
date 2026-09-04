"use client";

import { useEffect, useState } from "react";
import {
  FileText,
  Copy,
  Check,
  AlertTriangle,
  HelpCircle,
  ShieldCheck,
  Search,
  ExternalLink,
} from "lucide-react";
import { InvestigatorDossierResponse } from "@/types/investigation";
import { getTransactionDossier } from "@/lib/api";

interface InvestigatorDossierPanelProps {
  transactionId: string;
}

export function InvestigatorDossierPanel({ transactionId }: InvestigatorDossierPanelProps) {
  const [dossier, setDossier] = useState<InvestigatorDossierResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getTransactionDossier(transactionId).then((res) => {
      if (!isMounted) return;
      if (res.data) {
        setDossier(res.data);
      } else {
        setError(res.error || "Failed to load case dossier.");
      }
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [transactionId]);

  const handleCopyMarkdown = async () => {
    if (!dossier) return;
    try {
      await navigator.clipboard.writeText(dossier.markdown_dossier);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error("Failed to copy dossier:", err);
    }
  };

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] font-mono text-xs text-slate-400 animate-pulse">
        Synthesizing deterministic investigator dossier...
      </div>
    );
  }

  if (error || !dossier) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-rose-900/30 font-mono text-xs text-rose-400">
        Investigator dossier unavailable: {error}
      </div>
    );
  }

  return (
    <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4 font-mono text-xs select-none">
      {/* Header & Copy Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#142a32] pb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-cyan-400" />
          <div>
            <h3 className="font-bold text-white text-sm">
              Synthesized Investigator Dossier
            </h3>
            <div className="text-[10px] text-slate-400">
              Case ID: <span className="text-cyan-300 font-semibold">{dossier.case_id}</span>
            </div>
          </div>
        </div>

        <button
          onClick={handleCopyMarkdown}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950 hover:bg-cyan-900 border border-cyan-700/60 text-cyan-300 font-bold text-[11px] transition-all cursor-pointer w-fit"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-300">Copied to Clipboard!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy Investigator Dossier (Markdown)</span>
            </>
          )}
        </button>
      </div>

      {/* Executive Summary */}
      <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32] space-y-1">
        <div className="text-[11px] font-bold text-cyan-300 flex items-center gap-1.5">
          <Search className="w-3.5 h-3.5 text-cyan-400" />
          <span>Executive Case Brief</span>
        </div>
        <p className="text-slate-300 font-sans text-xs leading-relaxed">
          {dossier.executive_summary}
        </p>
      </div>

      {/* Corroborating Evidence Chain */}
      <div className="space-y-2">
        <div className="text-[11px] font-bold text-slate-300 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Corroborating Evidence Chain (Stage 9 Verified Signals)</span>
        </div>

        {dossier.corroborating_evidence_chain.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {dossier.corroborating_evidence_chain.map((ev) => (
              <div
                key={ev.evidence_id}
                className="p-3 rounded-lg bg-[#081216] border border-[#142a32] space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-[11.5px] truncate max-w-[200px]">
                    {ev.title}
                  </span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                      ev.severity === "HIGH"
                        ? "bg-rose-950/80 text-rose-300 border border-rose-800/40"
                        : ev.severity === "MEDIUM"
                        ? "bg-amber-950/80 text-amber-300 border border-amber-800/40"
                        : "bg-slate-800 text-slate-300"
                    }`}
                  >
                    {ev.severity}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
                  {ev.description}
                </p>
                <div className="pt-1 flex items-center justify-between text-[10px] text-slate-500">
                  <span className="font-mono">{ev.evidence_id}</span>
                  <span className="text-emerald-400 font-semibold">{ev.provenance_status}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32] text-slate-500 text-xs">
            No high-severity structural evidence items identified.
          </div>
        )}
      </div>

      {/* Potential Benign Explanations (Hypotheses) */}
      <div className="space-y-2">
        <div className="text-[11px] font-bold text-slate-300 flex items-center gap-1.5">
          <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
          <span>Potential Benign Explanations (Hypotheses)</span>
        </div>

        <div className="space-y-2">
          {dossier.potential_benign_explanations.map((hypo) => (
            <div
              key={hypo.hypothesis_id}
              className="p-3 rounded-lg bg-[#08151a] border border-amber-800/30 space-y-1"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-amber-300 text-xs">{hypo.title}</span>
                <span className="px-1.5 py-0.2 rounded text-[9px] bg-amber-950 text-amber-300 border border-amber-700/50">
                  {hypo.status}
                </span>
              </div>
              <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
                {hypo.description}
              </p>
              <div className="text-[10px] text-amber-400/80 font-mono pt-0.5">
                ⚠ {hypo.disclaimer}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommended Follow-up Verification (Strictly Human-in-the-Loop) */}
      <div className="space-y-2">
        <div className="text-[11px] font-bold text-slate-300 flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 text-cyan-400" />
          <span>Recommended Follow-up Verification (Non-Autonomous)</span>
        </div>

        <div className="space-y-1.5">
          {dossier.recommended_follow_up_inquiries.map((inq) => (
            <div
              key={inq.inquiry_id}
              className="p-2.5 rounded-lg bg-[#081216] border border-[#142a32] flex items-start gap-2.5 text-[11px]"
            >
              <span
                className={`px-1.5 py-0.5 rounded text-[9px] font-bold mt-0.5 shrink-0 ${
                  inq.priority === "HIGH"
                    ? "bg-rose-950 text-rose-300 border border-rose-800/40"
                    : inq.priority === "MEDIUM"
                    ? "bg-amber-950 text-amber-300 border border-amber-800/40"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                {inq.priority}
              </span>
              <div className="space-y-0.5">
                <div className="text-white font-semibold">{inq.recommended_action}</div>
                <div className="text-slate-400 text-[10px] font-sans">
                  Target: <span className="text-cyan-400 font-mono">{inq.target_entity_or_attribute}</span> | Purpose: {inq.verification_purpose}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Compliance Notice */}
      <div className="pt-2 border-t border-[#142a32] text-[10px] text-slate-500 font-sans leading-relaxed">
        {dossier.disclaimer}
      </div>
    </div>
  );
}
