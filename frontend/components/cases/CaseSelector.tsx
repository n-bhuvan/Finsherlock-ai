"use client";

import { useRouter } from "next/navigation";
import { Layers, ShieldCheck, AlertTriangle } from "lucide-react";

interface CaseSelectorProps {
  currentTransactionId: string;
}

const CASES = [
  {
    id: "TXN_00000203",
    label: "TXN_00000203",
    desc: "ACC_000213 • ₹99,500.00",
    badge: "HIGH RISK",
    color: "rose",
  },
  {
    id: "TXN_00000001",
    label: "TXN_00000001",
    desc: "ACC_000002 • ₹14,500.00",
    badge: "HIGH RISK",
    color: "rose",
  },
  {
    id: "TXN_00000646",
    label: "TXN_00000646",
    desc: "ACC_000054 • ₹1,159.95",
    badge: "LOW RISK",
    color: "emerald",
  },
  {
    id: "TXN_00000679",
    label: "TXN_00000679",
    desc: "ACC_000175 • ₹1,759.61",
    badge: "LOW RISK",
    color: "emerald",
  },
  {
    id: "TXN_00000500",
    label: "TXN_00000500",
    desc: "ACC_000456 • ₹764.87",
    badge: "LOW RISK",
    color: "cyan",
  },
];

export function CaseSelector({ currentTransactionId }: CaseSelectorProps) {
  const router = useRouter();

  return (
    <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-lg bg-[#071115] border border-[#142a32]">
      <div className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-mono text-slate-400">
        <Layers className="w-3.5 h-3.5 text-cyan-400" />
        <span>Verified Cases:</span>
      </div>

      {CASES.map((c) => {
        const isSelected = c.id === currentTransactionId;
        const isRisk = c.badge === "HIGH RISK";

        return (
          <button
            key={c.id}
            onClick={() => router.push(`/cases/${c.id}`)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-mono transition cursor-pointer ${
              isSelected
                ? "bg-[#0f2830] text-cyan-200 border border-cyan-500/50 shadow-sm"
                : "bg-[#0b161b] hover:bg-[#11232a] text-slate-400 hover:text-slate-200 border border-[#142a32]"
            }`}
          >
            {isRisk ? (
              <AlertTriangle className="w-3 h-3 text-rose-400 flex-shrink-0" />
            ) : (
              <ShieldCheck className="w-3 h-3 text-emerald-400 flex-shrink-0" />
            )}
            <span className="font-semibold">{c.id}</span>
            <span className="text-[10px] text-slate-500 hidden sm:inline">({c.desc})</span>
          </button>
        );
      })}
    </div>
  );
}
