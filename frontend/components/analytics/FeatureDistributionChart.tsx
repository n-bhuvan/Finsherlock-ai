"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Layers } from "lucide-react";

const FEATURE_DATA = [
  { group: "Transaction Attributes", count: 12, category: "Model A & B" },
  { group: "Behavioral Velocity", count: 25, category: "Model A & B" },
  { group: "Device Graph Co-Use", count: 7, category: "Model B Only" },
  { group: "IP Network Graph", count: 7, category: "Model B Only" },
  { group: "Beneficiary Topology", count: 7, category: "Model B Only" },
];

export function FeatureDistributionChart() {
  return (
    <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] space-y-3 font-mono text-xs select-none">
      <div className="flex items-center justify-between border-b border-[#142a32] pb-2.5">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <h3 className="font-bold text-white text-sm">
            Feature Space Architecture (37 Baseline vs 58 Graph)
          </h3>
        </div>
        <span className="text-[10px] text-slate-400">Total: 58 Features</span>
      </div>

      <p className="text-slate-400 text-xs font-sans">
        Breakdown of the 37 Model A features plus the 21 point-in-time graph features introduced in Model B:
      </p>

      <div className="h-64 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={FEATURE_DATA} margin={{ top: 10, right: 20, left: -10, bottom: 25 }}>
            <XAxis
              dataKey="group"
              tick={{ fill: "#94a3b8", fontSize: 10, fontFamily: "monospace" }}
              angle={-15}
              textAnchor="end"
            />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 10, fontFamily: "monospace" }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#08151c",
                borderColor: "#142a32",
                borderRadius: "8px",
                fontSize: "11px",
                fontFamily: "monospace",
                color: "#f8fafc",
              }}
              formatter={(value: any) => [`${value} features`, "Count"]}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {FEATURE_DATA.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.category === "Model B Only" ? "#06b6d4" : "#0d9488"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-center gap-6 text-[11px] pt-1">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-[#0d9488]" />
          <span className="text-slate-300">Baseline Features (37)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-[#06b6d4]" />
          <span className="text-cyan-300 font-semibold">Graph Features (21)</span>
        </div>
      </div>
    </div>
  );
}
