"use client";

import { useEffect, useState, useCallback } from "react";
import {
  MessageSquare,
  Send,
  Star,
  ShieldCheck,
  Hash,
  AlertTriangle,
  Clock,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";
import {
  FeedbackCategory,
  AnalystFeedbackRequest,
  AnalystFeedbackResponse,
} from "@/types/explanation";
import { submitAnalystFeedback, getTransactionFeedback } from "@/lib/api";

interface AnalystFeedbackCardProps {
  transactionId: string;
}

const CATEGORY_CONFIG: Record<
  FeedbackCategory,
  { label: string; color: string; description: string }
> = {
  EXPLANATION_USEFUL: {
    label: "Explanation Useful",
    color: "bg-emerald-950/70 border-emerald-700 text-emerald-300",
    description: "Grounding and reasoning accurately reflected case evidence",
  },
  OUTCOME_CONFIRMED: {
    label: "Outcome Confirmed",
    color: "bg-cyan-950/70 border-cyan-700 text-cyan-300",
    description: "Manual verification confirmed model risk classification",
  },
  INSUFFICIENT_EVIDENCE: {
    label: "Insufficient Evidence",
    color: "bg-amber-950/70 border-amber-700 text-amber-300",
    description: "Evidence items insufficient for conclusive assessment",
  },
  MISLEADING_EXPLANATION: {
    label: "Misleading Explanation",
    color: "bg-rose-950/70 border-rose-700 text-rose-300",
    description: "Explanation cited facts or interpretations that were ungrounded",
  },
  OUTCOME_CONTRADICTED: {
    label: "Outcome Contradicted",
    color: "bg-purple-950/70 border-purple-700 text-purple-300",
    description: "Ground-truth business outcome contradicted model prediction",
  },
};

export function AnalystFeedbackCard({ transactionId }: AnalystFeedbackCardProps) {
  const [category, setCategory] = useState<FeedbackCategory>("EXPLANATION_USEFUL");
  const [analystId, setAnalystId] = useState("senior_analyst_desk");
  const [notes, setNotes] = useState("");
  const [rating, setRating] = useState(5);
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [history, setHistory] = useState<AnalystFeedbackResponse[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const loadHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const res = await getTransactionFeedback(transactionId);
      if (res.data) {
        setHistory(res.data);
      }
    } catch {
      // ignore
    } finally {
      setLoadingHistory(false);
    }
  }, [transactionId]);

  useEffect(() => {
    loadHistory();
    setSubmitSuccess(null);
    setSubmitError(null);
  }, [transactionId, loadHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes.trim()) {
      setSubmitError("Please enter analyst observation notes.");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(null);

    const payload: AnalystFeedbackRequest = {
      transaction_id: transactionId,
      category,
      analyst_id: analystId.trim() || "analyst_desk",
      notes: notes.trim(),
      rating,
    };

    try {
      const res = await submitAnalystFeedback(payload);
      if (res.data) {
        setSubmitSuccess(
          `Feedback recorded! Audit Hash: ${res.data.audit_record_hash.slice(0, 16)}...`
        );
        setNotes("");
        await loadHistory();
      } else {
        setSubmitError(res.error || "Failed to submit feedback.");
      }
    } catch (err: any) {
      setSubmitError(err.message || "Failed to submit feedback.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4 font-mono text-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#142a32]">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white tracking-wide uppercase font-sans">
            Analyst Review &amp; Audit Feedback
          </h2>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950/70 border border-cyan-800 text-cyan-300">
            STAGE 21
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-emerald-400 flex items-center gap-1 font-bold">
            <ShieldCheck className="w-3.5 h-3.5" />
            Tamper-Evident SHA-256 Audit Chain
          </span>
        </div>
      </div>

      {/* Description */}
      <p className="text-slate-400 font-sans text-xs leading-relaxed">
        Record expert human review on model behavior, evidence grounding, or outcome confirmation.
        Feedback is cryptographically logged to the immutable audit chain.
      </p>

      {/* Feedback Submission Form */}
      <form onSubmit={handleSubmit} className="space-y-3 pt-1">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Category Selector */}
          <div>
            <label className="block text-[11px] text-slate-300 mb-1 font-sans font-bold">
              Review Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as FeedbackCategory)}
              className="w-full px-2.5 py-1.5 rounded-lg bg-[#071115] border border-[#142a32] text-white font-mono text-xs focus:border-cyan-500 focus:outline-none"
            >
              {Object.entries(CATEGORY_CONFIG).map(([catKey, cfg]) => (
                <option key={catKey} value={catKey}>
                  {cfg.label}
                </option>
              ))}
            </select>
          </div>

          {/* Analyst ID */}
          <div>
            <label className="block text-[11px] text-slate-300 mb-1 font-sans font-bold">
              Analyst Identifier
            </label>
            <input
              type="text"
              value={analystId}
              onChange={(e) => setAnalystId(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-lg bg-[#071115] border border-[#142a32] text-white font-mono text-xs focus:border-cyan-500 focus:outline-none"
              placeholder="analyst_id"
            />
          </div>

          {/* Rating Stars */}
          <div>
            <label className="block text-[11px] text-slate-300 mb-1 font-sans font-bold">
              Confidence / Quality Rating
            </label>
            <div className="flex items-center gap-1 py-1">
              {[1, 2, 3, 4, 5].map((starVal) => (
                <button
                  type="button"
                  key={starVal}
                  onClick={() => setRating(starVal)}
                  className={`p-1 rounded cursor-pointer transition ${
                    rating >= starVal ? "text-amber-400" : "text-slate-600 hover:text-slate-400"
                  }`}
                >
                  <Star className="w-4 h-4 fill-current" />
                </button>
              ))}
              <span className="ml-2 text-slate-300 font-mono text-xs">({rating}/5)</span>
            </div>
          </div>
        </div>

        {/* Observation Notes */}
        <div>
          <label className="block text-[11px] text-slate-300 mb-1 font-sans font-bold">
            Analyst Investigative Notes &amp; Findings
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            className="w-full px-3 py-2 rounded-lg bg-[#071115] border border-[#142a32] text-white font-mono text-xs focus:border-cyan-500 focus:outline-none leading-relaxed"
            placeholder="Document rationale, syndication verification, or observed counter-evidence. Inputs are sanitized against code injection."
          />
        </div>

        {/* Status Alerts */}
        {submitSuccess && (
          <div className="p-2 rounded bg-emerald-950/40 border border-emerald-800/80 text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
            <span>{submitSuccess}</span>
          </div>
        )}
        {submitError && (
          <div className="p-2 rounded bg-rose-950/40 border border-rose-800/80 text-rose-300 flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
            <span>{submitError}</span>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex items-center justify-between pt-1">
          <span className="text-[10px] text-slate-500 font-sans">
            Outputs sanitized &bull; Redaction active &bull; Human-review required
          </span>
          <button
            type="submit"
            disabled={submitting || !notes.trim()}
            className="px-4 py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-700/70 text-cyan-200 font-bold transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{submitting ? "Logging..." : "Submit to Audit Chain"}</span>
          </button>
        </div>
      </form>

      {/* Previously Logged Feedback Trail */}
      <div className="pt-2 border-t border-[#142a32]/60 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-slate-300 font-sans">
            Logged Feedback Trail ({history.length} record{history.length === 1 ? "" : "s"})
          </span>
          <button
            onClick={loadHistory}
            className="text-[10px] text-slate-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
          >
            <RefreshCw className={`w-3 h-3 ${loadingHistory ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {history.length === 0 ? (
          <div className="p-2.5 rounded bg-[#071115] border border-[#142a32] text-slate-500 text-[11px] text-center">
            No analyst feedback recorded for this case yet.
          </div>
        ) : (
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {history.map((item) => {
              const cfg =
                CATEGORY_CONFIG[item.category] || CATEGORY_CONFIG.EXPLANATION_USEFUL;
              return (
                <div
                  key={item.feedback_id}
                  className="p-2.5 rounded bg-[#071115] border border-[#142a32] space-y-1.5"
                >
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${cfg.color}`}
                      >
                        {cfg.label}
                      </span>
                      <span className="text-slate-300 font-mono text-[10px]">
                        {item.analyst_id}
                      </span>
                      <span className="text-amber-400 text-[10px]">
                        ★ {item.rating}/5
                      </span>
                    </div>
                    <span className="text-[9px] text-slate-500 flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5" />
                      {new Date(item.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-slate-300 text-[11px] font-sans leading-relaxed">
                    {item.notes}
                  </p>
                  <div className="flex items-center justify-between text-[9px] text-slate-500 pt-1 border-t border-[#142a32]/40 font-mono">
                    <span className="truncate max-w-xs">
                      ID: {item.feedback_id}
                    </span>
                    <span className="text-cyan-400 truncate max-w-xs">
                      Chain Hash: {item.audit_record_hash.slice(0, 16)}...
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
