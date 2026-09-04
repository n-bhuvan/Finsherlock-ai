import React from "react";
import { Handle, Position } from "@xyflow/react";
import {
  User,
  Smartphone,
  Wifi,
  Users,
  CreditCard,
  Building2,
} from "lucide-react";
import { GraphNodeData } from "@/types/graph";

function getNodeStyles(type: string, isFocus?: boolean) {
  if (isFocus) {
    return {
      border: "border-rose-500",
      bg: "bg-rose-950/80",
      text: "text-rose-200",
      glow: "shadow-[0_0_15px_rgba(244,63,94,0.3)]",
    };
  }
  switch (type) {
    case "account":
      return {
        border: "border-cyan-500/60",
        bg: "bg-cyan-950/60",
        text: "text-cyan-200",
        glow: "",
      };
    case "device":
      return {
        border: "border-emerald-500/60",
        bg: "bg-emerald-950/60",
        text: "text-emerald-200",
        glow: "",
      };
    case "ip":
      return {
        border: "border-amber-500/60",
        bg: "bg-amber-950/60",
        text: "text-amber-200",
        glow: "",
      };
    case "beneficiary":
      return {
        border: "border-purple-500/60",
        bg: "bg-purple-950/60",
        text: "text-purple-200",
        glow: "",
      };
    case "merchant":
      return {
        border: "border-blue-500/60",
        bg: "bg-blue-950/60",
        text: "text-blue-200",
        glow: "",
      };
    default:
      return {
        border: "border-slate-600",
        bg: "bg-slate-900",
        text: "text-slate-200",
        glow: "",
      };
  }
}

function getNodeIcon(type: string) {
  switch (type) {
    case "account":
      return <User className="w-3.5 h-3.5 text-cyan-400" />;
    case "device":
      return <Smartphone className="w-3.5 h-3.5 text-emerald-400" />;
    case "ip":
      return <Wifi className="w-3.5 h-3.5 text-amber-400" />;
    case "beneficiary":
      return <Users className="w-3.5 h-3.5 text-purple-400" />;
    case "merchant":
      return <Building2 className="w-3.5 h-3.5 text-blue-400" />;
    default:
      return <CreditCard className="w-3.5 h-3.5 text-rose-400" />;
  }
}

export const EntityNode = React.memo(({ data }: { data: GraphNodeData }) => {
  const styles = getNodeStyles(data.type, data.isFocus);

  return (
    <div
      className={`px-3 py-2 rounded-lg border ${styles.border} ${styles.bg} ${styles.glow} font-mono text-xs select-none min-w-[130px] transition hover:scale-105 cursor-pointer backdrop-blur-sm`}
    >
      <Handle type="target" position={Position.Top} className="!bg-cyan-500 !w-1.5 !h-1.5" />

      <div className="flex items-center gap-1.5 mb-1">
        {getNodeIcon(data.type)}
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          {data.type}
        </span>
      </div>

      <p className={`font-bold text-xs truncate ${styles.text}`}>
        {data.label}
      </p>

      {data.sublabel && (
        <p className="text-[10px] text-slate-400 truncate mt-0.5">
          {data.sublabel}
        </p>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-cyan-500 !w-1.5 !h-1.5" />
    </div>
  );
});

EntityNode.displayName = "EntityNode";
