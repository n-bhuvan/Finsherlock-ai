"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ScrollText,
  Clock,
  Database,
  AlertCircle,
  Trash2,
  ArrowRight,
  ShieldAlert,
  CheckCircle2,
} from "lucide-react";
import { SessionAuditEntry } from "@/types/audit";
import { ExplanationAuditView } from "@/components/audit/ExplanationAuditView";

export default function AuditPage() {
  const [entries, setEntries] = useState<SessionAuditEntry[]>([]);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem("ringguard_session_audit");
      if (raw) {
        setEntries(JSON.parse(raw));
      }
    } catch {
      // sessionStorage unavailable
    }
  }, []);

  const clearSessionAudit = () => {
    try {
      sessionStorage.removeItem("ringguard_session_audit");
      setEntries([]);
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-6 select-none font-mono text-xs">
      {/* 1. Header Banner */}
      <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#142a32] pb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <ScrollText className="w-4 h-4 text-cyan-400" />
              <h1 className="text-lg font-bold text-white font-sans tracking-wide">
                Investigation Audit Log
              </h1>
            </div>
            <p className="text-slate-400 text-xs font-sans">
              Transient browser session log recording real Stage 10 investigation tool calls:
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded bg-amber-950/60 border border-amber-700/50 text-amber-300 text-[10px] font-bold">
              Session Memory Only
            </span>
            {entries.length > 0 && (
              <button
                onClick={clearSessionAudit}
                className="px-2.5 py-1 rounded bg-[#081216] hover:bg-rose-950/50 border border-[#142a32] hover:border-rose-700 text-slate-400 hover:text-rose-300 transition flex items-center gap-1.5 cursor-pointer text-[11px]"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear</span>
              </button>
            )}
          </div>
        </div>

        {/* Boundary Notice */}
        <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32] text-[11px] text-slate-400 flex items-start gap-2 leading-relaxed">
          <AlertCircle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
          <p>
            <strong className="text-slate-300">Architecture Notice:</strong> Persistent server-side audit logging is not active in this MVP phase (Stages 1–10 enforce a strictly read-only database). Only real tools executed during the active browser session are displayed. Historical records are not simulated.
          </p>
        </div>
      </section>

      {/* 2. Audit Table or Empty State */}
      <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-[#142a32] pb-3">
          <h2 className="text-sm font-bold text-white font-sans">
            Executed Tool Invocations ({entries.length})
          </h2>
          <span className="text-[10px] text-slate-500">
            Source: In-Memory Client Session
          </span>
        </div>

        {entries.length === 0 ? (
          <div className="p-8 rounded-lg bg-[#081216] border border-[#142a32] text-center space-y-3">
            <ScrollText className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="space-y-1">
              <p className="text-slate-300 font-bold text-sm">No Session Invocations Recorded</p>
              <p className="text-slate-500 text-xs font-sans max-w-md mx-auto">
                Investigation tools executed in the Case Workspace will appear here in real time.
              </p>
            </div>
            <Link
              href="/cases/TXN_00000646"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0d262d] hover:bg-cyan-900/50 border border-cyan-500/40 text-cyan-300 text-xs font-semibold transition"
            >
              <span>Go to Hero Case Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#142a32] text-slate-400 text-[11px]">
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Tool Name</th>
                  <th className="py-2.5 px-3">Target ID</th>
                  <th className="py-2.5 px-3">Execution Status</th>
                  <th className="py-2.5 px-3">Result Count</th>
                  <th className="py-2.5 px-3">Linked Evidence IDs</th>
                  <th className="py-2.5 px-3 text-right">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#142a32]/60">
                {entries.map((entry) => (
                  <tr key={entry.id} className="hover:bg-[#081216]/80 transition">
                    <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                      {entry.timestamp.replace("T", " ").slice(0, 19)}
                    </td>
                    <td className="py-2.5 px-3 font-bold text-cyan-300">
                      {entry.tool_name}
                    </td>
                    <td className="py-2.5 px-3 text-white font-semibold">
                      {entry.target}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950/70 border border-emerald-700/60 text-emerald-300">
                        {entry.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">
                      {entry.result_count} items
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                      {entry.evidence_ids.length > 0 ? (
                        <span className="text-cyan-400">
                          {entry.evidence_ids.join(", ")}
                        </span>
                      ) : (
                        <span className="text-slate-600">None</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-400">
                      {entry.latency_ms}ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* 3. Stage 16: Cryptographic Explanation Audit Trail & Security Controls */}
      <ExplanationAuditView />
    </div>
  );
}
