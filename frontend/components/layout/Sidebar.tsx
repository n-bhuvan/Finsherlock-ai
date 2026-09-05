"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShieldAlert,
  LayoutDashboard,
  FolderGit2,
  Share2,
  BarChart3,
  ScrollText,
  Radio,
  Cpu,
} from "lucide-react";

const NAV_ITEMS = [
  {
    name: "Overview",
    href: "/",
    icon: LayoutDashboard,
    badge: null,
  },
  {
    name: "Cases",
    href: "/cases/TXN_00000203",
    icon: FolderGit2,
    badge: "Hero",
  },
  {
    name: "Networks",
    href: "/networks",
    icon: Share2,
    badge: null,
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: BarChart3,
    badge: null,
  },
  {
    name: "Audit",
    href: "/audit",
    icon: ScrollText,
    badge: "Session",
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#081216] border-r border-[#142a32] flex flex-col justify-between flex-shrink-0 min-h-screen text-slate-300 select-none">
      {/* Top Section: Brand & Navigation */}
      <div>
        {/* Brand Header */}
        <div className="h-16 border-b border-[#142a32] flex items-center px-5 gap-3 bg-[#060e12]">
          <div className="p-2 bg-cyan-950/70 border border-cyan-500/30 rounded-lg shadow-inner">
            <ShieldAlert className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="leading-tight">
            <span className="font-bold text-base text-white tracking-tight flex items-center gap-1.5">
              RingGuard
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-950 border border-cyan-800/60 text-cyan-300">
                AI
              </span>
            </span>
            <span className="text-[11px] text-slate-400 block">Risk Operations Center</span>
          </div>
        </div>

        {/* Navigation Section */}
        <div className="px-3 py-4 space-y-1">
          <p className="px-3 text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold mb-2">
            Operations
          </p>

          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href.split("/")[1] ? `/${item.href.split("/")[1]}` : item.href);

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition group ${
                  isActive
                    ? "bg-[#0d262d] text-cyan-300 border border-cyan-500/40 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#0c1a20]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`w-4 h-4 transition ${
                      isActive ? "text-cyan-400" : "text-slate-500 group-hover:text-slate-300"
                    }`}
                  />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                      isActive
                        ? "bg-cyan-950 text-cyan-300 border border-cyan-700/50"
                        : "bg-[#11242b] text-slate-400 border border-[#1a3843]"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Bottom Section: Telemetry & Status */}
      <div className="p-4 border-t border-[#142a32] bg-[#060e12]/60 space-y-3">
        <div className="flex items-center justify-between text-[11px] font-mono">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            Live Gateway
          </span>
          <span className="text-emerald-400">8000/TCP</span>
        </div>

        <div className="p-2.5 rounded-lg bg-[#0b151b] border border-[#142a32] text-[11px] space-y-1">
          <div className="flex justify-between items-center text-slate-400 font-mono text-[10px]">
            <span>ENGINE:</span>
            <span className="text-cyan-400">XGBoost v1 (58-feat)</span>
          </div>
          <div className="flex justify-between items-center text-slate-400 font-mono text-[10px]">
            <span>DATABASE:</span>
            <span className="text-slate-300">PostgreSQL (2k txs)</span>
          </div>
        </div>

        <div className="text-[10px] text-slate-400 text-center flex flex-col items-center justify-center gap-0.5">
          <div className="flex items-center gap-1 text-slate-400">
            <Cpu className="w-3 h-3 text-cyan-400" />
            <span>Track 02 — AI Risk Manager</span>
          </div>
          <span className="text-[9px] text-amber-400/80 font-mono">Synthetic Data Prototype</span>
        </div>
      </div>
    </aside>
  );
}
