"use client";

import { useState } from "react";
import { UserCheck, ShieldAlert, AlertCircle, FileSearch, CheckCircle2 } from "lucide-react";

export function HumanDecision() {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);

  return (
    <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4 select-none">
      <div className="flex items-center justify-between border-b border-[#142a32] pb-3">
        <div className="flex items-center gap-2">
          <UserCheck className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">
            Human Decision &amp; Case Review
          </h2>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/70 text-amber-300 border border-amber-700/50">
          Awaiting Human Review
        </span>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed">
        RingGuard AI is a defense-only decision support tool. Autonomous account blocking and fund confiscation are prohibited. Select a recommended disposition based on the verified evidence and graph context:
      </p>

      {/* Action Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          onClick={() => setSelectedAction("APPROVE")}
          className={`px-4 py-2.5 rounded-lg border text-xs font-mono font-semibold transition cursor-pointer flex items-center justify-center gap-2 ${
            selectedAction === "APPROVE"
              ? "bg-emerald-950/80 border-emerald-500 text-emerald-200 shadow-sm"
              : "bg-[#081216] border-[#142a32] text-slate-300 hover:bg-emerald-950/30 hover:border-emerald-600/50"
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          Approve Transaction
        </button>

        <button
          onClick={() => setSelectedAction("REQUEST_EVIDENCE")}
          className={`px-4 py-2.5 rounded-lg border text-xs font-mono font-semibold transition cursor-pointer flex items-center justify-center gap-2 ${
            selectedAction === "REQUEST_EVIDENCE"
              ? "bg-cyan-950/80 border-cyan-500 text-cyan-200 shadow-sm"
              : "bg-[#081216] border-[#142a32] text-slate-300 hover:bg-cyan-950/30 hover:border-cyan-600/50"
          }`}
        >
          <FileSearch className="w-3.5 h-3.5 text-cyan-400" />
          Request Evidence
        </button>

        <button
          onClick={() => setSelectedAction("ESCALATE")}
          className={`px-4 py-2.5 rounded-lg border text-xs font-mono font-semibold transition cursor-pointer flex items-center justify-center gap-2 ${
            selectedAction === "ESCALATE"
              ? "bg-rose-950/80 border-rose-500 text-rose-200 shadow-sm"
              : "bg-[#081216] border-[#142a32] text-slate-300 hover:bg-rose-950/30 hover:border-rose-600/50"
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
          Escalate to Fraud Team
        </button>
      </div>

      {selectedAction && (
        <div className="p-3 rounded-lg bg-[#08161d] border border-[#142a32] text-xs font-mono text-slate-300 flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>Deliberation Selected: <strong className="text-cyan-300">{selectedAction}</strong></span>
          </span>
          <span className="text-[11px] text-amber-400 font-sans">
            Review workspace only — no database mutation or automated enforcement executed.
          </span>
        </div>
      )}

      {/* Non-Persistence Disclaimer Notice */}
      <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32] text-[11px] text-slate-400 flex items-start gap-2">
        <AlertCircle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-slate-300">Defense-Only &amp; Human-in-the-Loop:</strong> RingGuard AI does not execute autonomous payment blocking or account freezes. Dispositions are recorded for human analyst review only; persistent audit database storage is inactive in this read-only MVP phase.
        </p>
      </div>
    </section>
  );
}
