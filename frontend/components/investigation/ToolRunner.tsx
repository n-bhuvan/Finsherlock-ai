"use client";

import { useState } from "react";
import {
  Wrench,
  Smartphone,
  Wifi,
  Users,
  GitFork,
  Cpu,
  User,
  ShieldAlert,
} from "lucide-react";
import {
  investigateAccount,
  investigateSharedDevices,
  investigateSharedIPs,
  investigateCommonBeneficiaries,
  investigateRelatedAccounts,
  investigateTransactionFundFlow,
  investigateRiskFeatures,
} from "@/lib/api";
import { ToolExecutionResult } from "@/types/investigation";
import { SessionAuditEntry } from "@/types/audit";
import { ToolResultCard } from "./ToolResultCard";

interface ToolRunnerProps {
  transactionId: string;
  accountId: string;
  onAuditLog?: (entry: SessionAuditEntry) => void;
}

export function ToolRunner({
  transactionId,
  accountId,
  onAuditLog,
}: ToolRunnerProps) {
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [result, setResult] = useState<ToolExecutionResult<any> | null>(null);
  const [loading, setLoading] = useState(false);

  const runTool = async (
    toolName: string,
    action: () => Promise<{ data: ToolExecutionResult<any> | null; error: string | null; latencyMs: number }>
  ) => {
    setActiveTool(toolName);
    setLoading(true);
    setResult(null);

    const res = await action();
    setLoading(false);

    if (res.data) {
      setResult(res.data);
      if (onAuditLog) {
        onAuditLog({
          id: `AUDIT_${Date.now()}`,
          timestamp: new Date().toISOString(),
          tool_name: res.data.tool_name,
          target: res.data.target,
          status: res.data.status,
          result_count: res.data.result_count,
          source: res.data.source,
          evidence_ids: res.data.evidence_ids || [],
          latency_ms: res.latencyMs,
        });
      }
    } else {
      setResult({
        tool_name: toolName,
        status: "UNAVAILABLE",
        target: transactionId,
        result: null,
        result_count: 0,
        source: "backend.investigation",
        evidence_ids: [],
        error_details: res.error,
        disclaimer: "Tool execution failed or returned an error.",
      });
    }
  };

  return (
    <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4 select-none">
      <div className="flex items-center justify-between border-b border-[#142a32] pb-3">
        <div className="flex items-center gap-2">
          <Wrench className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">
            Controlled Investigation Tools
          </h2>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/70 text-cyan-300 border border-cyan-700/50">
          Stage 10 Read-Only Suite
        </span>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed font-sans">
        Execute deterministic, bounded investigation tools against live database records. Read-only, zero enforcement actions, zero LLM calls:
      </p>

      {/* Tool Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        <button
          onClick={() => runTool("get_account", () => investigateAccount(accountId))}
          disabled={loading}
          className="p-2.5 rounded-lg bg-[#081216] border border-[#142a32] hover:border-cyan-500/50 hover:bg-[#0c1a20] transition text-left cursor-pointer space-y-1 group"
        >
          <User className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition" />
          <span className="text-[11px] font-mono font-bold text-white block">Account</span>
          <span className="text-[10px] text-slate-500 block">Metadata</span>
        </button>

        <button
          onClick={() => runTool("find_shared_devices", () => investigateSharedDevices(accountId))}
          disabled={loading}
          className="p-2.5 rounded-lg bg-[#081216] border border-[#142a32] hover:border-emerald-500/50 hover:bg-[#0c1a20] transition text-left cursor-pointer space-y-1 group"
        >
          <Smartphone className="w-3.5 h-3.5 text-emerald-400 group-hover:scale-110 transition" />
          <span className="text-[11px] font-mono font-bold text-white block">Devices</span>
          <span className="text-[10px] text-slate-500 block">Hardware Co-Use</span>
        </button>

        <button
          onClick={() => runTool("find_shared_ips", () => investigateSharedIPs(accountId))}
          disabled={loading}
          className="p-2.5 rounded-lg bg-[#081216] border border-[#142a32] hover:border-amber-500/50 hover:bg-[#0c1a20] transition text-left cursor-pointer space-y-1 group"
        >
          <Wifi className="w-3.5 h-3.5 text-amber-400 group-hover:scale-110 transition" />
          <span className="text-[11px] font-mono font-bold text-white block">IP Addrs</span>
          <span className="text-[10px] text-slate-500 block">Network Co-Use</span>
        </button>

        <button
          onClick={() => runTool("find_common_beneficiaries", () => investigateCommonBeneficiaries(accountId))}
          disabled={loading}
          className="p-2.5 rounded-lg bg-[#081216] border border-[#142a32] hover:border-purple-500/50 hover:bg-[#0c1a20] transition text-left cursor-pointer space-y-1 group"
        >
          <Users className="w-3.5 h-3.5 text-purple-400 group-hover:scale-110 transition" />
          <span className="text-[11px] font-mono font-bold text-white block">Beneficiaries</span>
          <span className="text-[10px] text-slate-500 block">Common Payees</span>
        </button>

        <button
          onClick={() => runTool("find_related_accounts", () => investigateRelatedAccounts(accountId))}
          disabled={loading}
          className="p-2.5 rounded-lg bg-[#081216] border border-[#142a32] hover:border-cyan-500/50 hover:bg-[#0c1a20] transition text-left cursor-pointer space-y-1 group"
        >
          <Users className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition" />
          <span className="text-[11px] font-mono font-bold text-white block">Related</span>
          <span className="text-[10px] text-slate-500 block">Peer Accounts</span>
        </button>

        <button
          onClick={() => runTool("trace_fund_flow", () => investigateTransactionFundFlow(transactionId))}
          disabled={loading}
          className="p-2.5 rounded-lg bg-[#081216] border border-[#142a32] hover:border-rose-500/50 hover:bg-[#0c1a20] transition text-left cursor-pointer space-y-1 group"
        >
          <GitFork className="w-3.5 h-3.5 text-rose-400 group-hover:scale-110 transition" />
          <span className="text-[11px] font-mono font-bold text-white block">Fund Flow</span>
          <span className="text-[10px] text-slate-500 block">Transaction Hops</span>
        </button>

        <button
          onClick={() => runTool("get_risk_features", () => investigateRiskFeatures(transactionId, "graph"))}
          disabled={loading}
          className="p-2.5 rounded-lg bg-[#081216] border border-[#142a32] hover:border-cyan-500/50 hover:bg-[#0c1a20] transition text-left cursor-pointer space-y-1 group"
        >
          <Cpu className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition" />
          <span className="text-[11px] font-mono font-bold text-white block">58 Features</span>
          <span className="text-[10px] text-slate-500 block">Model Vector</span>
        </button>
      </div>

      {/* Render Active Tool Result */}
      {(loading || result) && (
        <ToolResultCard
          result={result}
          loading={loading}
          onClose={() => setResult(null)}
        />
      )}
    </section>
  );
}
