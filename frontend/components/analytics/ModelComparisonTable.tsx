import { GitCompare, HelpCircle, CheckCircle2, ShieldAlert } from "lucide-react";

export function ModelComparisonTable() {
  const metrics = [
    { name: "PR-AUC", modelA: "1.0000", modelB: "1.0000", delta: "0.0000" },
    { name: "ROC-AUC", modelA: "1.0000", modelB: "1.0000", delta: "0.0000" },
    { name: "Precision", modelA: "1.0000", modelB: "1.0000", delta: "0.0000" },
    { name: "Recall", modelA: "1.0000", modelB: "1.0000", delta: "0.0000" },
    { name: "F1 Score", modelA: "1.0000", modelB: "1.0000", delta: "0.0000" },
    { name: "False Positive Rate", modelA: "0.0000", modelB: "0.0000", delta: "0.0000" },
  ];

  return (
    <div className="space-y-4 font-mono text-xs select-none">
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#142a32] pb-3">
          <div className="flex items-center gap-2">
            <GitCompare className="w-4 h-4 text-cyan-400" />
            <h3 className="font-bold text-white text-sm">
              Held-Out Synthetic Evaluation (Stage 6 &amp; 7 Benchmark Artifacts)
            </h3>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-950/80 text-cyan-300 border border-cyan-700/50 w-fit">
            Provenance: ml/data/evaluation/model_comparison.json
          </span>
        </div>

        {/* Metrics Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#142a32] text-slate-400 text-[11px]">
                <th className="py-2 px-3">Metric</th>
                <th className="py-2 px-3">Model A (Baseline — 37 Feat)</th>
                <th className="py-2 px-3">Model B (Graph — 58 Feat)</th>
                <th className="py-2 px-3">Measured Delta</th>
                <th className="py-2 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#142a32]/60 text-slate-300">
              {metrics.map((m) => (
                <tr key={m.name} className="hover:bg-[#081216]">
                  <td className="py-2.5 px-3 font-semibold text-white">{m.name}</td>
                  <td className="py-2.5 px-3 text-slate-300">{m.modelA}</td>
                  <td className="py-2.5 px-3 text-cyan-300 font-bold">{m.modelB}</td>
                  <td className="py-2.5 px-3 text-slate-400">{m.delta}</td>
                  <td className="py-2.5 px-3">
                    <span className="inline-flex items-center gap-1 text-emerald-400 text-[10px]">
                      <CheckCircle2 className="w-3 h-3" /> Parity Ceiling
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Confusion Matrix Breakdown */}
        <div className="pt-3 border-t border-[#142a32] grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
          <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32] space-y-1">
            <span className="text-slate-400 font-bold block">Model A Confusion Matrix (Test Split n=300):</span>
            <div className="flex justify-between text-slate-300">
              <span>True Negatives: 245</span>
              <span>False Positives: 0</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>False Negatives: 0</span>
              <span>True Positives: 55</span>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-[#081216] border border-[#142a32] space-y-1">
            <span className="text-cyan-300 font-bold block">Model B Confusion Matrix (Test Split n=300):</span>
            <div className="flex justify-between text-slate-300">
              <span>True Negatives: 245</span>
              <span>False Positives: 0</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>False Negatives: 0</span>
              <span>True Positives: 55</span>
            </div>
          </div>
        </div>

        {/* Technical Explanatory Note */}
        <div className="p-3.5 rounded-lg bg-[#08161d] border border-cyan-500/30 text-[11px] text-slate-300 space-y-1 leading-relaxed">
          <div className="flex items-center gap-1.5 text-cyan-400 font-bold">
            <HelpCircle className="w-4 h-4" />
            <span>Factual Technical Notice (Zero Graph Uplift Claim)</span>
          </div>
          <p className="font-sans text-slate-400">
            The held-out synthetic test set achieved a metric ceiling where the measured classification delta is <strong>0.0000</strong>. Because synthetic abuse-ring scenarios feature strong separability, the baseline Model A already reaches 1.0 PR-AUC. The primary architectural benefit of Model B in this phase is extracting and validating the <strong>21 point-in-time graph features</strong> that enable Stage 9 automated evidence synthesis and Stage 10 investigation tools.
          </p>
        </div>
      </div>
    </div>
  );
}
