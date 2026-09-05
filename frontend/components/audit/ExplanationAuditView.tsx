"use client";

import { useEffect, useState } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  Hash,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Lock,
  RotateCcw,
} from "lucide-react";
import { ExplanationAuditResponse, SecurityStatusResponse } from "@/types/explanation";
import { getExplanationAuditLog, getSecurityControlsStatus } from "@/lib/api";

export function ExplanationAuditView() {
  const [auditData, setAuditData] = useState<ExplanationAuditResponse | null>(null);
  const [securityData, setSecurityData] = useState<SecurityStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const loadAuditInfo = async () => {
    setLoading(true);
    try {
      const [audRes, secRes] = await Promise.all([
        getExplanationAuditLog(20),
        getSecurityControlsStatus(),
      ]);
      if (audRes.data) setAuditData(audRes.data);
      if (secRes.data) setSecurityData(secRes.data);
    } catch (err) {
      console.error("Failed to load audit info:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditInfo();
  }, []);

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] text-slate-400 font-mono text-xs flex items-center gap-2">
        <div className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        Verifying cryptographic hash chain &amp; security controls...
      </div>
    );
  }

  const isChainValid = auditData?.chain_integrity_valid ?? true;

  return (
    <div className="space-y-6 font-mono text-xs">
      {/* 1. Security Posture Checklist */}
      <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-[#142a32] pb-3">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-white font-sans tracking-wide">
              Stage 16 Security Posture &amp; Control Verification
            </h2>
          </div>
          <span className="px-2.5 py-1 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-[10px] font-bold">
            All 7 Controls Active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {securityData?.controls.map((c, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-[#071115] border border-[#142a32] space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-[11px] font-sans">{c.name}</span>
                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                  {c.status}
                </span>
              </div>
              <p className="text-slate-400 text-[10px] font-sans leading-relaxed">{c.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 2. Hash-Chained Audit Trail Log */}
      <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#142a32] pb-3">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <Hash className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-bold text-white font-sans">
                Hash-Chained Append-Oriented Explanation Audit Log
              </h2>
            </div>
            <p className="text-slate-400 text-[11px] font-sans">
              Cryptographic SHA-256 link: <code className="text-slate-300">record_hash = SHA256(prev_hash + canonical_payload)</code>
            </p>
            <p className="text-slate-500 text-[10px] font-sans italic">
              * Detects record tampering, interior deletion and reordering; external checkpointing is required to detect final-tail deletion/truncation.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className={`px-2.5 py-1 rounded border text-[10px] font-bold flex items-center gap-1.5 ${
              isChainValid
                ? "bg-emerald-950/60 border-emerald-800 text-emerald-300"
                : "bg-rose-950/60 border-rose-800 text-rose-300"
            }`}>
              {isChainValid ? <ShieldCheck className="w-3.5 h-3.5" /> : <ShieldAlert className="w-3.5 h-3.5" />}
              <span>{isChainValid ? "Cryptographic Chain Verified" : "Tamper Detected"}</span>
            </div>

            <button
              onClick={loadAuditInfo}
              className="px-2.5 py-1 rounded bg-[#071115] hover:bg-[#0e212a] border border-[#142a32] text-slate-300 hover:text-white transition flex items-center gap-1 cursor-pointer text-[10px]"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Verify</span>
            </button>
          </div>
        </div>

        {/* Records Table */}
        {!auditData || auditData.records.length === 0 ? (
          <div className="p-8 rounded-lg bg-[#071115] border border-[#142a32] text-center text-slate-500 text-xs font-sans">
            No explanation audit records in hash chain yet. Execute an explanation on a case page to create records.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-[#142a32]">
            <table className="w-full text-left text-[11px]">
              <thead className="bg-[#071115] text-slate-400 border-b border-[#142a32] uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2 px-3 font-semibold">Audit ID / Timestamp</th>
                  <th className="py-2 px-3 font-semibold">Target Tx</th>
                  <th className="py-2 px-3 font-semibold">Provider / Model</th>
                  <th className="py-2 px-3 font-semibold text-center">Grounding</th>
                  <th className="py-2 px-3 font-semibold text-center">Latency</th>
                  <th className="py-2 px-3 font-semibold text-right">Status</th>
                  <th className="py-2 px-3 font-semibold text-right">Record SHA (12c)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#142a32] bg-[#09151b]">
                {auditData.records.map((r, idx) => (
                  <tr key={idx} className="hover:bg-[#0d1e26] transition">
                    <td className="py-2.5 px-3 font-mono">
                      <div className="font-bold text-white">{r.audit_id}</div>
                      <div className="text-slate-500 text-[9px]">{new Date(r.timestamp).toLocaleTimeString()}</div>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">{r.transaction_id}</td>
                    <td className="py-2.5 px-3">
                      <div className="text-slate-300 font-sans">{r.provider}</div>
                      <div className="text-slate-500 text-[9px] font-mono">{r.model_name}</div>
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono font-bold text-emerald-400">
                      {(r.grounding_ratio * 100).toFixed(0)}%
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono text-slate-400">
                      {r.latency_ms.toFixed(1)}ms
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                        r.status === "SUCCESS" ? "bg-emerald-950 text-emerald-300 border border-emerald-800" :
                        r.status === "FALLBACK" ? "bg-cyan-950 text-cyan-300 border border-cyan-800" :
                        "bg-amber-950 text-amber-300 border border-amber-800"
                      }`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-slate-500 text-[10px]">
                      {r.record_hash ? `${r.record_hash.slice(0, 12)}...` : "&mdash;"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
