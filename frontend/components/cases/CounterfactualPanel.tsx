"use client";

import { useEffect, useState } from "react";
import {
  Sparkles,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  Sliders,
  Shield,
  Info,
  HelpCircle,
  Activity,
  CheckCircle2,
  AlertCircle,
  RotateCcw,
} from "lucide-react";
import {
  CounterfactualAnalysisResponse,
  CounterfactualAttribution,
  CounterfactualIntervention,
} from "@/types/counterfactual";
import { getCounterfactualAnalysis, simulateCustomIntervention } from "@/lib/api";

interface CounterfactualPanelProps {
  transactionId: string;
}

export function CounterfactualPanel({ transactionId }: CounterfactualPanelProps) {
  const [data, setData] = useState<CounterfactualAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Custom simulation state
  const [customFeature, setCustomFeature] = useState<string>("tx_amount");
  const [customValue, setCustomValue] = useState<string>("942");
  const [customResult, setCustomResult] = useState<CounterfactualIntervention | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [customError, setCustomError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);
    setCustomResult(null);

    getCounterfactualAnalysis(transactionId).then((res) => {
      if (!isMounted) return;
      if (res.data) {
        setData(res.data);
      } else {
        setError(res.error || "Failed to load counterfactual analysis.");
      }
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [transactionId]);

  const handleSimulate = async () => {
    const val = parseFloat(customValue);
    if (isNaN(val)) {
      setCustomError("Please enter a valid numeric value.");
      return;
    }
    setSimulating(true);
    setCustomError(null);

    const res = await simulateCustomIntervention(transactionId, customFeature, val);
    if (res.data) {
      setCustomResult(res.data);
    } else {
      setCustomError(res.error || "Simulation failed.");
    }
    setSimulating(false);
  };

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-[#0e1626] border border-[#1b2844] text-slate-400 font-mono text-xs flex items-center gap-2 animate-pulse">
        <Sparkles className="w-4 h-4 text-indigo-400 animate-spin" />
        <span>Computing Model B TreeSHAP counterfactual attributions and hypothetical interventions...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 rounded-xl bg-[#0e1626] border border-slate-800 text-slate-400 font-mono text-xs flex items-center gap-2">
        <Info className="w-4 h-4 text-slate-500 shrink-0" />
        <span>Counterfactual Analysis: {error || "Unavailable"}</span>
      </div>
    );
  }

  const topAttributions = data.attributions.slice(0, 6);

  return (
    <div className="rounded-xl bg-gradient-to-b from-[#0e1626] to-[#0a0f1d] border border-[#1e293b] p-5 shadow-xl space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-white tracking-wide">
                Counterfactual Attribution & Intervention Simulation
              </h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Stage 18
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Deterministic What-If model sensitivity analysis · Read-only decision support
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap text-[11px] font-mono">
          <div className="px-2.5 py-1 rounded-md bg-slate-800/80 text-slate-300 border border-slate-700">
            Orig Model B: <span className="text-cyan-400 font-bold">{(data.original_risk_score * 100).toFixed(1)}%</span>
          </div>
          <div className="px-2.5 py-1 rounded-md bg-emerald-950/40 text-emerald-300 border border-emerald-800/50">
            Defense-Only
          </div>
        </div>
      </div>

      {/* Grid: Top Drivers & What-If Interventions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Col: Top Model Drivers (TreeSHAP) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              Top Model Drivers (TreeSHAP)
            </span>
            <span className="text-[10px] font-mono text-slate-500">Margin Log-Odds</span>
          </div>

          <div className="space-y-2">
            {topAttributions.map((attr) => {
              const isIncrease = attr.direction === "INCREASES_RISK";
              const isDecrease = attr.direction === "DECREASES_RISK";
              return (
                <div
                  key={attr.feature_name}
                  className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="text-slate-200 font-medium truncate max-w-[200px]" title={attr.feature_name}>
                      {attr.attribution_rank}. {attr.feature_name}
                    </span>
                    <span
                      className={`font-bold ${
                        isIncrease ? "text-rose-400" : isDecrease ? "text-emerald-400" : "text-slate-400"
                      }`}
                    >
                      {attr.contribution > 0 ? `+${attr.contribution.toFixed(3)}` : attr.contribution.toFixed(3)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Observed: <span className="text-slate-300 font-mono">{attr.actual_value}</span></span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-medium ${
                        isIncrease
                          ? "bg-rose-500/10 text-rose-300 border border-rose-500/20"
                          : isDecrease
                          ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                          : "bg-slate-700/40 text-slate-400 border border-slate-700"
                      }`}
                    >
                      {attr.direction}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col: What-If Standard Interventions */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              Hypothetical Interventions (Simulated Sensitivity)
            </span>
            <span className="text-[10px] font-mono text-slate-500">Δ Calibrated Risk</span>
          </div>

          <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
            {data.interventions.map((inv) => {
              const deltaPct = (inv.risk_delta * 100).toFixed(1);
              const isSignificantDrop = inv.risk_delta <= -0.10;
              const isZero = Math.abs(inv.risk_delta) < 0.0001;

              return (
                <div
                  key={inv.intervention_id}
                  className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-colors space-y-1.5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-slate-200">
                        {inv.intervention_id.replace("INT_", "").replace(/_/g, " ")}
                      </span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold ${
                          inv.plausibility_status === "PLAUSIBLE"
                            ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30"
                            : "bg-violet-500/10 text-violet-300 border border-violet-500/30"
                        }`}
                      >
                        {inv.plausibility_status}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="text-slate-400">{(inv.original_risk_score * 100).toFixed(1)}%</span>
                      <ArrowRight className="w-3 h-3 text-slate-500" />
                      <span className="text-slate-200 font-bold">{(inv.counterfactual_risk_score * 100).toFixed(1)}%</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                          isSignificantDrop
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : isZero
                            ? "bg-slate-800 text-slate-400"
                            : inv.risk_delta < 0
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-rose-500/10 text-rose-400"
                        }`}
                      >
                        {inv.risk_delta > 0 ? `+${deltaPct}%` : `${deltaPct}%`}
                      </span>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    {inv.assumption}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Interactive Custom Perturbation Simulator */}
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-indigo-400" />
            Custom Feature What-If Simulator
          </span>
          <span className="text-[10px] text-slate-500 font-mono">Whitelisted Features Only</span>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <select
            value={customFeature}
            onChange={(e) => {
              setCustomFeature(e.target.value);
              if (e.target.value === "tx_amount") setCustomValue("942");
              else if (e.target.value === "g_shared_device_accounts_count") setCustomValue("0");
              else if (e.target.value === "beh_rolling_tx_count_1h") setCustomValue("0");
              else setCustomValue("0");
            }}
            className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="tx_amount">tx_amount (Transaction Amount ₹)</option>
            <option value="g_shared_device_accounts_count">g_shared_device_accounts_count (Shared Devices)</option>
            <option value="g_shared_ip_accounts_count">g_shared_ip_accounts_count (Shared IPs)</option>
            <option value="g_connected_accounts_count">g_connected_accounts_count (Connected Accounts)</option>
            <option value="beh_rolling_tx_count_1h">beh_rolling_tx_count_1h (1h Tx Velocity)</option>
            <option value="beh_rolling_tx_count_24h">beh_rolling_tx_count_24h (24h Tx Velocity)</option>
            <option value="g_degree">g_degree (Network Graph Degree)</option>
            <option value="transaction_id">transaction_id (Blacklisted Test)</option>
          </select>

          <input
            type="number"
            value={customValue}
            onChange={(e) => setCustomValue(e.target.value)}
            placeholder="Hypothetical value"
            className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 w-full sm:w-40 focus:outline-none focus:border-indigo-500"
          />

          <button
            onClick={handleSimulate}
            disabled={simulating}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium tracking-wide transition-colors flex items-center justify-center gap-1.5 shrink-0 disabled:opacity-50"
          >
            {simulating ? (
              <>
                <Sparkles className="w-3.5 h-3.5 animate-spin" />
                Simulating...
              </>
            ) : (
              <>
                <Sliders className="w-3.5 h-3.5" />
                Simulate What-If
              </>
            )}
          </button>
        </div>

        {customError && (
          <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-mono flex items-center gap-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{customError}</span>
          </div>
        )}

        {customResult && (
          <div className="p-3 rounded-lg bg-indigo-950/20 border border-indigo-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
            <div>
              <span className="text-slate-400">Hypothetical: </span>
              <span className="text-white font-bold">{customResult.feature_name} = {customResult.counterfactual_value}</span>
              <span className="text-slate-500 mx-2">|</span>
              <span className="text-slate-400">Status: </span>
              <span className="text-cyan-300 font-semibold">{customResult.plausibility_status}</span>
              <p className="text-[11px] text-slate-400 font-sans mt-1">{customResult.assumption}</p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <span className="text-slate-400">{(customResult.original_risk_score * 100).toFixed(1)}%</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-white font-bold">{(customResult.counterfactual_risk_score * 100).toFixed(1)}%</span>
              <span
                className={`px-2 py-0.5 rounded text-xs font-bold ${
                  customResult.risk_delta <= -0.05
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : customResult.risk_delta > 0
                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                {customResult.risk_delta > 0
                  ? `+${(customResult.risk_delta * 100).toFixed(1)}%`
                  : `${(customResult.risk_delta * 100).toFixed(1)}%`}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Mandatory Scientific Disclaimer & Read-Only Governance Notice */}
      <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex items-start gap-2.5 text-[11px] text-slate-400">
        <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-medium text-slate-300">
            Scientific & Governance Disclaimer:
          </p>
          <p>
            Counterfactual results are model-sensitivity simulations, not causal claims and not predictions of what would necessarily happen in the real world. Original Model B production risk scores and database records remain immutable. Zero autonomous financial actions or blocking decisions are executed.
          </p>
        </div>
      </div>
    </div>
  );
}
