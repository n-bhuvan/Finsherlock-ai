"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Lock,
} from "lucide-react";
import { checkBackendHealth } from "@/lib/api";

const QUICK_CASES = [
  { id: "TXN_00000203", label: "TXN_00000203 (₹99,500.00)", type: "HIGH RISK" },
  { id: "TXN_00000001", label: "TXN_00000001 (₹14,500.00)", type: "HIGH RISK" },
  { id: "TXN_00000646", label: "TXN_00000646 (₹1,159.95)", type: "LOW RISK" },
  { id: "TXN_00000500", label: "TXN_00000500 (₹764.87)", type: "LOW RISK" },
];

export function Header() {
  const router = useRouter();
  const [searchInput, setSearchInput] = useState("");
  const [isOnline, setIsOnline] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  const probe = useCallback(async () => {
    setIsChecking(true);
    const res = await checkBackendHealth();
    setIsOnline(res.data?.status === "ok");
    setIsChecking(false);
  }, []);

  useEffect(() => {
    probe();
    const interval = setInterval(probe, 15000);
    return () => clearInterval(interval);
  }, [probe]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = searchInput.trim().toUpperCase();
    if (clean) {
      router.push(`/cases/${clean}`);
      setSearchInput("");
    }
  };

  return (
    <header className="h-16 border-b border-[#142a32] bg-[#071014] px-6 flex items-center justify-between gap-4 select-none">
      {/* Search Input & Quick Cases */}
      <div className="flex items-center gap-3 flex-1 max-w-xl">
        <form onSubmit={handleSearch} className="relative flex-1">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search transaction ID (e.g. TXN_00000646) or account ID..."
            className="w-full bg-[#0b161b] border border-[#142a32] rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/40 transition font-mono"
          />
        </form>

        <div className="hidden lg:flex items-center gap-1.5 text-[11px] font-mono">
          <span className="text-slate-500 text-[10px]">Triage:</span>
          {QUICK_CASES.slice(0, 2).map((c) => (
            <button
              key={c.id}
              onClick={() => router.push(`/cases/${c.id}`)}
              className="px-2 py-1 rounded bg-[#0b161b] hover:bg-[#11242b] border border-[#142a32] text-slate-300 hover:text-cyan-300 transition text-[10px] cursor-pointer"
            >
              {c.id}
            </button>
          ))}
        </div>
      </div>

      {/* Gateway Telemetry & Defense Boundary */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#0a181e] border border-[#142a32] text-[11px] text-slate-400 font-mono">
          <Lock className="w-3 h-3 text-cyan-400" />
          <span>Defense-Only Boundary</span>
        </div>

        {/* Backend Health Badge */}
        <div
          onClick={probe}
          title="Click to re-verify backend connectivity"
          className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#0b161b] border border-[#142a32] text-xs font-mono cursor-pointer hover:border-slate-700 transition"
        >
          {isChecking ? (
            <>
              <RefreshCw className="w-3 h-3 text-cyan-400 animate-spin" />
              <span className="text-cyan-400 text-[11px]">Probing...</span>
            </>
          ) : isOnline ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-300 text-[11px]">Backend Online</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
              <span className="text-rose-300 text-[11px]">Gateway Offline</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
