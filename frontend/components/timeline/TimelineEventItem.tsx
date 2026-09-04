import { TimelineEvent } from "@/types/timeline";
import {
  Calendar,
  CreditCard,
  UserPlus,
  ArrowRightLeft,
  Users,
  Database,
} from "lucide-react";

interface TimelineEventItemProps {
  event: TimelineEvent;
  isLast: boolean;
}

function getTimelineIcon(type: string) {
  switch (type) {
    case "ACCOUNT_CREATED":
      return <UserPlus className="w-3.5 h-3.5 text-cyan-400" />;
    case "LARGE_INCOMING_TRANSACTION":
    case "TRANSACTION":
      return <CreditCard className="w-3.5 h-3.5 text-emerald-400" />;
    case "RAPID_TRANSFER":
      return <ArrowRightLeft className="w-3.5 h-3.5 text-rose-400" />;
    case "CONNECTED_ACCOUNT_ACTIVITY":
      return <Users className="w-3.5 h-3.5 text-amber-400" />;
    default:
      return <Calendar className="w-3.5 h-3.5 text-slate-400" />;
  }
}

export function TimelineEventItem({ event, isLast }: TimelineEventItemProps) {
  const isHigh = event.severity === "HIGH";

  return (
    <div className="relative flex items-start gap-3 text-xs font-mono">
      {/* Vertical Connecting Line */}
      {!isLast && (
        <div className="absolute left-[15px] top-7 bottom-0 w-[1px] bg-[#193843]" />
      )}

      {/* Node Dot */}
      <div
        className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 z-10 border ${
          isHigh
            ? "bg-rose-950/80 border-rose-600/60 shadow-sm"
            : "bg-[#081216] border-[#1a3843]"
        }`}
      >
        {getTimelineIcon(event.event_type)}
      </div>

      {/* Event Details Card */}
      <div className="flex-1 p-3 rounded-lg bg-[#081216] border border-[#142a32] space-y-1.5 hover:border-cyan-500/40 transition">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 border-b border-[#142a32]/60 pb-1.5">
          <span className="font-semibold text-white font-sans text-xs flex items-center gap-1.5">
            {event.title}
          </span>
          <span className="text-[11px] text-cyan-400 font-mono">
            {event.timestamp.replace("T", " ").slice(0, 19)}
          </span>
        </div>

        <p className="text-slate-300 font-sans text-xs leading-relaxed">
          {event.description}
        </p>

        {/* Footer: Table source & supporting record IDs */}
        <div className="pt-1.5 border-t border-[#142a32]/60 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-500">
          <div className="flex items-center gap-1">
            <Database className="w-3 h-3 text-slate-500" />
            <span title={`Source column: ${event.timestamp_source}`}>
              {event.timestamp_source}
            </span>
          </div>

          {event.supporting_record_ids.length > 0 && (
            <div className="flex items-center gap-1">
              <span>IDs:</span>
              <span className="text-slate-400">
                {event.supporting_record_ids.join(", ")}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
