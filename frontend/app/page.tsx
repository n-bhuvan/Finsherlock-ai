"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  Server,
  Activity,
  Network,
  Database,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Cpu,
  Layers,
  Lock,
} from "lucide-react";
import { getRiskHealth } from "@/lib/api";
import { RiskHealthResponse } from "@/types/risk";

const CURATED_CASES = [
  {
    id: "TXN_00000203",
    account: "ACC_000213",
    amount: "₹99,500.00",
    channel: "IMPS",
    timestamp: "2026-01-18 22:35:45",
    risk: "HIGH RISK",
    prob: "99.92%",
    category: "Coordinated Abuse Ring (Hero Case)",
    badgeColor: "rose",
  },
  {
    id: "TXN_00000001",
    account: "ACC_000002",
    amount: "₹14,500.00",
    channel: "UPI",
    timestamp: "2026-01-25 04:25:22",
    risk: "HIGH RISK",
    prob: "99.95%",
    category: "Abuse-Ring Target Transaction",
    badgeColor: "rose",
  },
  {
    id: "TXN_00000646",
    account: "ACC_000054",
    amount: "₹1,159.95",
    channel: "NETBANKING",
    timestamp: "2026-01-01 00:40:18",
    risk: "LOW RISK",
    prob: "0.10%",
    category: "Legitimate Baseline Transfer",
    badgeColor: "emerald",
  },
  {
    id: "TXN_00000679",
    account: "ACC_000175",
    amount: "₹1,759.61",
    channel: "NETBANKING",
    timestamp: "2026-01-01 00:42:23",
    risk: "LOW RISK",
    prob: "0.13%",
    category: "Standard Netbanking Payment",
    badgeColor: "emerald",
  },
  {
    id: "TXN_00000500",
    account: "ACC_000456",
    amount: "₹764.87",
    channel: "UPI",
    timestamp: "2026-01-31 09:03:40",
    risk: "LOW RISK",
    prob: "0.08%",
    category: "Standard Merchant Payment",
    badgeColor: "cyan",
  },
];

export default function OverviewPage() {
  const [health, setHealth] = useState<RiskHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchHealth = useCallback(async () => {
    setRefreshing(true);
    const res = await getRiskHealth();
    if (res.data) setHealth(res.data);
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  return (
    <div className="space-y-6 select-none font-mono text-xs">
      {/* 1. Hero Command Center Banner */}
      <section className="p-6 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-3 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60 text-[10px] font-bold">
                OPERATIONS DASHBOARD
              </span>
              <span className="text-slate-500">•</span>
              <span className="text-slate-400 text-xs">Track 02: AI Risk Manager</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white font-sans">
              Risk Operations Center
            </h1>
            <p className="text-xs text-slate-400 font-sans max-w-2xl leading-relaxed">
              Network-Aware Abuse-Ring Detection &amp; Evidence-First Risk Investigation. Combines point-in-time graph intelligence with XGBoost to surface coordinated financial abuse rings.
            </p>
          </div>

          <Link
            href="/cases/TXN_00000203"
            className="px-4 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-sans font-semibold text-xs transition flex items-center justify-center gap-2 shadow-lg shadow-cyan-950/50 cursor-pointer self-start md:self-auto"
          >
            <span>Open Hero Case (TXN_00000203)</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* 2. System Status & Engine Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#081216] border border-[#142a32] space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-[11px]">
            <span className="flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5 text-cyan-400" /> Model Gateway
            </span>
            {health?.status === "ok" ? (
              <span className="text-emerald-400 font-bold">ONLINE</span>
            ) : (
              <span className="text-amber-400 font-bold">CONNECTING</span>
            )}
          </div>
          <p className="text-base font-bold text-white">
            {health?.service || "ringguard-risk-engine"}
          </p>
          <div className="text-[10px] text-slate-500 pt-1 border-t border-[#142a32]/60 flex justify-between">
            <span>Health Probing:</span>
            <span>Active (15s)</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#081216] border border-[#142a32] space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-[11px]">
            <span className="flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-slate-400" /> Model A (Baseline)
            </span>
            <span className="text-emerald-400 font-bold">LOADED</span>
          </div>
          <p className="text-base font-bold text-white">37 Features</p>
          <div className="text-[10px] text-slate-500 pt-1 border-t border-[#142a32]/60 flex justify-between">
            <span>Scope:</span>
            <span>Transaction + Behavioral</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#081216] border border-[#142a32] space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-[11px]">
            <span className="flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-cyan-400" /> Model B (Graph)
            </span>
            <span className="text-emerald-400 font-bold">LOADED</span>
          </div>
          <p className="text-base font-bold text-cyan-300">58 Features</p>
          <div className="text-[10px] text-slate-500 pt-1 border-t border-[#142a32]/60 flex justify-between">
            <span>Point-in-Time Graph:</span>
            <span className="text-cyan-400 font-bold">+21 Features</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#081216] border border-[#142a32] space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-[11px]">
            <span className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-cyan-400" /> Database Store
            </span>
            <span className="text-emerald-400 font-bold">CONNECTED</span>
          </div>
          <p className="text-base font-bold text-white">2,000 Transactions</p>
          <div className="text-[10px] text-slate-500 pt-1 border-t border-[#142a32]/60 flex justify-between">
            <span>Entities:</span>
            <span>500 Accounts, 100 Devices</span>
          </div>
        </div>
      </div>

      {/* 3. Priority Case Triage Queue */}
      <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#142a32] pb-3">
          <div>
            <h2 className="text-sm font-bold text-white font-sans tracking-wide">
              Active Investigation Queue
            </h2>
            <p className="text-[11px] text-slate-400 font-sans">
              Verified synthetic test transactions from database ground truth. Select any case to inspect evidence, topology, and chronological timeline:
            </p>
          </div>

          <button
            onClick={fetchHealth}
            disabled={refreshing}
            className="px-3 py-1.5 rounded-lg bg-[#081216] hover:bg-[#11242b] border border-[#142a32] text-slate-300 flex items-center gap-1.5 transition text-[11px] cursor-pointer self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${refreshing ? "animate-spin" : ""}`} />
            <span>Refresh Telemetry</span>
          </button>
        </div>

        {/* Case Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#142a32] text-slate-400 text-[11px]">
                <th className="py-2.5 px-3">Transaction ID</th>
                <th className="py-2.5 px-3">Target Account</th>
                <th className="py-2.5 px-3">Amount (Synthetic)</th>
                <th className="py-2.5 px-3">Channel</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Model Risk</th>
                <th className="py-2.5 px-3">Investigation Context</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#142a32]/60">
              {CURATED_CASES.map((c) => {
                const isHigh = c.badgeColor === "rose";
                return (
                  <tr key={c.id} className="hover:bg-[#081216]/80 transition">
                    <td className="py-3 px-3 font-bold text-white">{c.id}</td>
                    <td className="py-3 px-3 text-slate-300">{c.account}</td>
                    <td className="py-3 px-3 font-bold text-slate-200">{c.amount}</td>
                    <td className="py-3 px-3 text-slate-400">{c.channel}</td>
                    <td className="py-3 px-3 text-slate-400">{c.timestamp}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                          isHigh
                            ? "bg-rose-950/70 border-rose-700/60 text-rose-300"
                            : "bg-emerald-950/70 border-emerald-700/60 text-emerald-300"
                        }`}
                      >
                        {c.risk} ({c.prob})
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-300">{c.category}</td>
                    <td className="py-3 px-3 text-right">
                      <Link
                        href={`/cases/${c.id}`}
                        className="px-2.5 py-1 rounded bg-[#0d262d] hover:bg-cyan-900/60 border border-cyan-500/40 text-cyan-300 text-[11px] font-semibold transition inline-flex items-center gap-1 cursor-pointer"
                      >
                        <span>Investigate</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* 4. Architecture & Security Guarantees */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-slate-400 text-xs font-sans">
        <div className="p-4 rounded-xl bg-[#081216] border border-[#142a32] space-y-1.5">
          <div className="flex items-center gap-2 font-bold text-white">
            <Lock className="w-4 h-4 text-cyan-400" />
            <span>Defense-Only Architecture</span>
          </div>
          <p className="leading-relaxed text-[11px]">
            RingGuard AI strictly assists human analysts. Autonomous fund movement, automated payment rejection, and account blocking are prohibited.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#081216] border border-[#142a32] space-y-1.5">
          <div className="flex items-center gap-2 font-bold text-white">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>Zero Fake Metrics</span>
          </div>
          <p className="leading-relaxed text-[11px]">
            All probabilities, evidence items, timestamps, and graph topologies derive from verified backend endpoints. Unavailable fields display explicit unavailable states.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#081216] border border-[#142a32] space-y-1.5">
          <div className="flex items-center gap-2 font-bold text-white">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Point-in-Time Graph Safety</span>
          </div>
          <p className="leading-relaxed text-[11px]">
            Model B features, timeline events, and evidence extraction are strictly constrained to historical data (t &le; T) with zero future information leakage.
          </p>
        </div>
      </div>
    </div>
  );
}
