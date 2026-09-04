import { TimelineResponse } from "@/types/timeline";
import { TimelineEventItem } from "./TimelineEventItem";
import { History, ShieldAlert, AlertCircle } from "lucide-react";
import { formatProbability } from "@/lib/format";

interface TimelineViewProps {
  timeline: TimelineResponse | null;
  loading: boolean;
  error: string | null;
}

export function TimelineView({ timeline, loading, error }: TimelineViewProps) {
  if (loading) {
    return (
      <div className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] animate-pulse space-y-4">
        <div className="h-5 bg-[#11242b] rounded w-1/4" />
        <div className="space-y-4">
          <div className="h-16 bg-[#11242b] rounded" />
          <div className="h-16 bg-[#11242b] rounded" />
          <div className="h-16 bg-[#11242b] rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-5 rounded-xl bg-[#0b151b] border border-rose-900/40 text-xs font-mono text-rose-300 space-y-2">
        <div className="flex items-center gap-2 font-bold">
          <AlertCircle className="w-4 h-4 text-rose-400" />
          Unable to reconstruct timeline
        </div>
        <p className="text-slate-400">{error}</p>
      </div>
    );
  }

  const events = timeline?.events || [];

  return (
    <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4 select-none">
      <div className="flex items-center justify-between border-b border-[#142a32] pb-3">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">
            Chronological Activity Timeline
          </h2>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#11242b] text-cyan-300 border border-[#193843]">
          {events.length} Historical Events
        </span>
      </div>

      {events.length === 0 ? (
        <div className="p-6 rounded-lg bg-[#081216] border border-[#142a32] text-center text-xs font-mono text-slate-400">
          No historical events recorded prior to the investigation timestamp.
        </div>
      ) : (
        <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
          {events.map((event, idx) => (
            <TimelineEventItem
              key={event.event_id}
              event={event}
              isLast={idx === events.length - 1}
            />
          ))}
        </div>
      )}

      {/* Isolated Derived Risk Context Callout */}
      {timeline?.risk_context && (
        <div className="p-3 rounded-lg bg-[#08161d] border border-cyan-500/30 text-[11px] font-mono text-slate-300 space-y-1">
          <div className="flex items-center gap-1.5 text-cyan-400 font-semibold text-xs">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Derived Model Risk Context (Isolated from Historical Events)</span>
          </div>
          <p className="text-slate-400 text-[11px] font-sans">
            Evaluated by Model B: Probability {formatProbability(timeline.risk_context.predicted_ring_probability)} ({String(timeline.risk_context.risk_band || "UNKNOWN")}). Model evaluations represent derived system assessments and are strictly separated from factual transaction events.
          </p>
        </div>
      )}
    </section>
  );
}
