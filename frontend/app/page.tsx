"use client";

import { useEffect, useState, useCallback } from "react";
import { checkBackendHealth } from "@/lib/api";
import { BackendStatus } from "@/types/api";
import {
  ShieldAlert,
  Server,
  MonitorCheck,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Terminal,
  Cpu,
  Layers,
  FileCode,
  ExternalLink,
} from "lucide-react";

export default function HomePage() {
  const [status, setStatus] = useState<BackendStatus>({
    state: "checking",
    data: null,
    error: null,
    latencyMs: null,
    lastChecked: null,
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchHealth = useCallback(async () => {
    setIsRefreshing(true);
    setStatus((prev) => ({ ...prev, state: "checking" }));
    const result = await checkBackendHealth();

    if (result.data && result.data.status === "ok") {
      setStatus({
        state: "connected",
        data: result.data,
        error: null,
        latencyMs: result.latencyMs,
        lastChecked: new Date(),
      });
    } else {
      setStatus({
        state: "not_connected",
        data: null,
        error: result.error,
        latencyMs: result.latencyMs,
        lastChecked: new Date(),
      });
    }
    setIsRefreshing(false);
  }, []);

  useEffect(() => {
    fetchHealth();
    // Poll health periodically every 10 seconds
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  return (
    <main className="min-h-screen flex flex-col justify-between p-6 sm:p-12 max-w-6xl mx-auto text-slate-100">
      {/* Top Header Bar */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-sky-950/60 border border-sky-500/30 rounded-lg shadow-inner">
            <ShieldAlert className="w-6 h-6 text-sky-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              RingGuard AI
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-950 border border-sky-800/50 text-sky-300">
                Track 02 — AI Risk Manager
              </span>
            </h1>
            <p className="text-xs text-slate-400">Razorpay AI Buildathon 2026</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-slate-900 border border-slate-700 text-slate-300 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
            Stage 1: Foundation
          </span>
        </div>
      </header>

      {/* Hero Section */}
      <section className="my-10 space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-semibold tracking-wide uppercase">
          <AlertCircle className="w-3.5 h-3.5" />
          MVP FOUNDATION
        </div>

        <div className="space-y-3">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white">
            RingGuard AI
          </h2>
          <p className="text-lg sm:text-xl text-slate-300 max-w-3xl font-medium leading-relaxed">
            Network-Aware Abuse-Ring Detection &amp;
            <br className="hidden sm:inline" /> Evidence-First Risk Investigation
          </p>
        </div>

        <p className="text-sm text-slate-400 max-w-2xl leading-relaxed">
          A defense-only AI risk investigation architecture for detecting coordinated
          payment abuse and mule-account syndicates through graph intelligence,
          machine learning, and human-in-the-loop decision support.
        </p>
      </section>

      {/* Operational Status Verification Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
        {/* Frontend Status Card */}
        <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 shadow-xl backdrop-blur-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <MonitorCheck className="w-5 h-5 text-emerald-400" />
              <span className="text-sm font-semibold text-slate-200">
                Frontend Client
              </span>
            </div>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950/80 border border-emerald-700/60 text-emerald-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Online
            </span>
          </div>

          <div className="pt-2 border-t border-slate-800/80 text-xs text-slate-400 space-y-1 font-mono">
            <p className="flex justify-between">
              <span>Stack:</span>
              <span className="text-slate-300">Next.js (App Router) + TypeScript</span>
            </p>
            <p className="flex justify-between">
              <span>Port:</span>
              <span className="text-slate-300">3000</span>
            </p>
          </div>
        </div>

        {/* Backend Status Card */}
        <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 shadow-xl backdrop-blur-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Server className="w-5 h-5 text-sky-400" />
              <span className="text-sm font-semibold text-slate-200">
                Backend Gateway
              </span>
            </div>

            {/* Live Connection Badges */}
            {status.state === "checking" && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-sky-950/80 border border-sky-700/60 text-sky-300">
                <RefreshCw className="w-3 h-3 animate-spin" />
                Checking...
              </span>
            )}
            {status.state === "connected" && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950/80 border border-emerald-700/60 text-emerald-300">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Connected
              </span>
            )}
            {status.state === "not_connected" && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-950/80 border border-rose-700/60 text-rose-300">
                <XCircle className="w-3.5 h-3.5" />
                Not Connected
              </span>
            )}
          </div>

          <div className="pt-2 border-t border-slate-800/80 text-xs text-slate-400 space-y-1 font-mono">
            <p className="flex justify-between">
              <span>Target:</span>
              <span className="text-slate-300 truncate max-w-[200px]" title={`${apiUrl}/health`}>
                {apiUrl}/health
              </span>
            </p>
            <p className="flex justify-between">
              <span>Response:</span>
              {status.state === "connected" ? (
                <span className="text-emerald-400">
                  {status.data?.service} ({status.latencyMs}ms)
                </span>
              ) : status.state === "checking" ? (
                <span className="text-sky-400">Probing...</span>
              ) : (
                <span className="text-rose-400 truncate max-w-[200px]" title={status.error || "Offline"}>
                  {status.error || "Offline"}
                </span>
              )}
            </p>
          </div>
        </div>
      </section>

      {/* Manual Health Probe Control Bar */}
      <section className="p-4 rounded-lg bg-slate-900/40 border border-slate-800/60 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-400">
          <Terminal className="w-4 h-4 text-slate-500" />
          <span>
            {status.lastChecked ? (
              <>
                Last verified:{" "}
                <span className="text-slate-300 font-mono">
                  {status.lastChecked.toLocaleTimeString()}
                </span>
              </>
            ) : (
              "Waiting for initial health probe..."
            )}
          </span>
        </div>

        <button
          onClick={fetchHealth}
          disabled={isRefreshing}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 active:bg-slate-600 text-slate-200 border border-slate-700 transition disabled:opacity-50 cursor-pointer text-xs font-medium"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`}
          />
          Verify Connection
        </button>
      </section>

      {/* Architecture & Boundaries Notice */}
      <section className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div className="p-4 rounded-lg bg-slate-900/30 border border-slate-800/60 space-y-2">
          <div className="flex items-center gap-2 font-semibold text-slate-300">
            <Layers className="w-4 h-4 text-sky-400" />
            Modular Monolith
          </div>
          <p className="text-slate-400 leading-relaxed">
            FastAPI backend with structured modules for Graph Intelligence, XGBoost Model,
            Evidence Synthesis, and Audit Logging.
          </p>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/30 border border-slate-800/60 space-y-2">
          <div className="flex items-center gap-2 font-semibold text-slate-300">
            <Cpu className="w-4 h-4 text-sky-400" />
            Zero Fake Metrics
          </div>
          <p className="text-slate-400 leading-relaxed">
            Stage 1 contains no placeholder cases, mock graphs, or hardcoded probabilities.
            All analytics will derive from actual models in later stages.
          </p>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/30 border border-slate-800/60 space-y-2">
          <div className="flex items-center gap-2 font-semibold text-slate-300">
            <FileCode className="w-4 h-4 text-sky-400" />
            Human Authority
          </div>
          <p className="text-slate-400 leading-relaxed">
            Defense-only investigation support. No autonomous fund movements,
            automated approvals, or autonomous blocking.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-10 pt-6 border-t border-slate-800/60 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-2">
        <p>RingGuard AI © 2026 — Track 02: AI Risk Manager</p>
        <div className="flex items-center gap-4">
          <a
            href={`${apiUrl}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-sky-400 transition flex items-center gap-1"
          >
            FastAPI Docs <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </footer>
    </main>
  );
}
