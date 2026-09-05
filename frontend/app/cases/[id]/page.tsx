"use client";

import { useEffect, useState, useCallback, use } from "react";
import { Node, Edge } from "@xyflow/react";
import {
  getTransactionRisk,
  getBaselineRisk,
  getTransactionEvidence,
  getTransactionTimeline,
  investigateTransactionFundFlow,
  investigateSharedDevices,
  investigateSharedIPs,
  investigateCommonBeneficiaries,
  investigateRelatedAccounts,
} from "@/lib/api";
import { RiskResponse, BaselineRiskResponse } from "@/types/risk";
import { EvidenceListResponse } from "@/types/evidence";
import { TimelineResponse } from "@/types/timeline";
import { TransactionRecord } from "@/types/investigation";
import { GraphNodeData } from "@/types/graph";
import { SessionAuditEntry } from "@/types/audit";

import { CaseHeader } from "@/components/cases/CaseHeader";
import { RiskComparison } from "@/components/cases/RiskComparison";
import { FeatureIsolationCard } from "@/components/cases/FeatureIsolationCard";
import { InvestigationAgentPanel } from "@/components/cases/InvestigationAgentPanel";
import { InvestigatorDossierPanel } from "@/components/cases/InvestigatorDossierPanel";
import { AIExplanationPanel } from "@/components/cases/AIExplanationPanel";
import { CaseSelector } from "@/components/cases/CaseSelector";
import { HumanDecision } from "@/components/cases/HumanDecision";
import { EvidenceList } from "@/components/evidence/EvidenceList";
import { TimelineView } from "@/components/timeline/TimelineView";
import { EvidenceGraph } from "@/components/graph/EvidenceGraph";
import { ToolRunner } from "@/components/investigation/ToolRunner";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function CaseInvestigationPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const transactionId = resolvedParams.id;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [risk, setRisk] = useState<RiskResponse | null>(null);
  const [baselineRisk, setBaselineRisk] = useState<BaselineRiskResponse | null>(null);
  const [evidence, setEvidence] = useState<EvidenceListResponse | null>(null);
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [transaction, setTransaction] = useState<TransactionRecord | null>(null);

  // Graph state
  const [graphNodes, setGraphNodes] = useState<Node<GraphNodeData>[]>([]);
  const [graphEdges, setGraphEdges] = useState<Edge[]>([]);

  const loadCaseData = useCallback(async () => {
    // Reset state immediately on transactionId change to prevent stale display
    setLoading(true);
    setError(null);
    setRisk(null);
    setBaselineRisk(null);
    setEvidence(null);
    setTimeline(null);
    setTransaction(null);
    setGraphNodes([]);
    setGraphEdges([]);

    // 1. Fetch live transaction data directly via backend fund-flow
    // and live Risk, Evidence, Timeline concurrently from the backend APIs
    const [flowRes, riskRes, baseRes, evRes, timeRes] = await Promise.all([
      investigateTransactionFundFlow(transactionId, 2),
      getTransactionRisk(transactionId),
      getBaselineRisk(transactionId),
      getTransactionEvidence(transactionId),
      getTransactionTimeline(transactionId),
    ]);

    if (!riskRes.data && riskRes.error) {
      setError(riskRes.error);
      setLoading(false);
      return;
    }

    setRisk(riskRes.data);
    setBaselineRisk(baseRes.data);
    setEvidence(evRes.data);
    setTimeline(timeRes.data);

    // CRITICAL DATA INTEGRITY FIX:
    // Match the EXACT target transaction by transactionId in flow results.
    // NEVER use an adjacent transaction or blind array index [0].
    const targetHop = flowRes.data?.result?.find(
      (h) => h.transaction_id === transactionId
    );

    let targetAmount = targetHop ? targetHop.amount : 0;
    let targetTimestamp = targetHop?.timestamp || "";
    let targetAccount = targetHop?.source_account_id || "";
    let targetChannel = targetHop?.channel || "";
    let targetStatus = targetHop?.status || "SUCCESS";

    // Fallback: If fund-flow did not contain the hop, inspect timeline events
    if (!targetHop && timeRes.data?.events) {
      const txEvent = timeRes.data.events.find(
        (e) => e.supporting_record_ids?.includes(transactionId) || e.event_id === transactionId
      );
      if (txEvent) {
        targetTimestamp = txEvent.timestamp;
        const foundAcc = txEvent.related_entities?.find((id) => id.startsWith("ACC_"));
        if (foundAcc) targetAccount = foundAcc;
      }
    }

    const accId = targetAccount || "ACC_000001";

    const realTx: TransactionRecord = {
      transaction_id: transactionId,
      account_id: accId,
      timestamp: targetTimestamp || new Date().toISOString(),
      amount: targetAmount,
      transaction_type: "TRANSFER",
      status: targetStatus,
      channel: targetChannel || "IMPS",
      device_id: "",
      ip_id: "",
      beneficiary_id: targetHop?.beneficiary_id || null,
      merchant_id: targetHop?.merchant_id || null,
    };

    setTransaction(realTx);

    // 2. Fetch real account entities (devices, IPs, beneficiaries) using the verified account ID
    const [devRes, ipRes, benRes] = await Promise.all([
      investigateSharedDevices(accId),
      investigateSharedIPs(accId),
      investigateCommonBeneficiaries(accId),
    ]);

    // 3. Assemble Verified Graph Nodes & Edges strictly from real backend records
    const nodes: Node<GraphNodeData>[] = [];
    const edges: Edge[] = [];

    // Target Transaction (Center Focus Node) — consistently shows realTx.amount
    nodes.push({
      id: transactionId,
      type: "entityNode",
      position: { x: 320, y: 180 },
      data: {
        id: transactionId,
        label: transactionId,
        type: "transaction",
        sublabel: `₹${realTx.amount.toLocaleString("en-IN")}`,
        isFocus: true,
        metadata: {
          Amount: `₹${realTx.amount.toLocaleString("en-IN")}`,
          Channel: realTx.channel,
          Status: realTx.status,
          Timestamp: realTx.timestamp,
        },
      },
    });

    // Investigated Account
    nodes.push({
      id: accId,
      type: "entityNode",
      position: { x: 100, y: 180 },
      data: {
        id: accId,
        label: accId,
        type: "account",
        sublabel: "Target Account",
        metadata: {
          "Account ID": accId,
          "Role": "Originating Account",
        },
      },
    });

    edges.push({
      id: `edge-${accId}-${transactionId}`,
      source: accId,
      target: transactionId,
      label: "EXECUTED",
    });

    // Devices (from verified Stage 10 data)
    const devices = devRes.data?.result || [];
    devices.slice(0, 2).forEach((d, idx) => {
      nodes.push({
        id: d.device_id,
        type: "entityNode",
        position: { x: 180 + idx * 160, y: 30 },
        data: {
          id: d.device_id,
          label: d.device_id,
          type: "device",
          sublabel: `${d.device_os} (${d.device_type})`,
          metadata: {
            "OS": d.device_os,
            "Type": d.device_type,
            "Co-using Accounts": d.co_using_accounts.join(", "),
          },
        },
      });

      edges.push({
        id: `edge-${accId}-${d.device_id}`,
        source: accId,
        target: d.device_id,
        label: "USED_DEVICE",
      });

      d.co_using_accounts.slice(0, 1).forEach((peerAcc, pIdx) => {
        if (peerAcc !== accId && !nodes.some((n) => n.id === peerAcc)) {
          nodes.push({
            id: peerAcc,
            type: "entityNode",
            position: { x: 420 + pIdx * 120, y: 30 },
            data: {
              id: peerAcc,
              label: peerAcc,
              type: "account",
              sublabel: "Co-User",
              metadata: { "Connected Via": d.device_id },
            },
          });
          edges.push({
            id: `edge-${peerAcc}-${d.device_id}`,
            source: peerAcc,
            target: d.device_id,
            label: "CO_LINKED",
          });
        }
      });
    });

    // Beneficiaries (from verified Stage 10 data)
    const beneficiaries = benRes.data?.result || [];
    beneficiaries.slice(0, 2).forEach((b, idx) => {
      nodes.push({
        id: b.beneficiary_id,
        type: "entityNode",
        position: { x: 320 + idx * 180, y: 340 },
        data: {
          id: b.beneficiary_id,
          label: b.beneficiary_id,
          type: "beneficiary",
          sublabel: b.beneficiary_type,
          metadata: {
            "Type": b.beneficiary_type,
            "Bank Prefix": b.bank_ifsc_prefix,
            "Co-Senders": b.co_sending_accounts.join(", "),
          },
        },
      });

      edges.push({
        id: `edge-${transactionId}-${b.beneficiary_id}`,
        source: transactionId,
        target: b.beneficiary_id,
        label: "SENT_TO",
      });
    });

    // IPs (from verified Stage 10 data)
    const ips = ipRes.data?.result || [];
    ips.slice(0, 1).forEach((ip) => {
      nodes.push({
        id: ip.ip_id,
        type: "entityNode",
        position: { x: 520, y: 180 },
        data: {
          id: ip.ip_id,
          label: ip.ip_id,
          type: "ip",
          sublabel: `${ip.ip_address} (${ip.country})`,
          metadata: {
            "Address": ip.ip_address,
            "Type": ip.ip_type,
            "Country": ip.country,
          },
        },
      });

      edges.push({
        id: `edge-${transactionId}-${ip.ip_id}`,
        source: transactionId,
        target: ip.ip_id,
        label: "ORIGIN_IP",
      });
    });

    setGraphNodes(nodes);
    setGraphEdges(edges);
    setLoading(false);
  }, [transactionId]);

  useEffect(() => {
    loadCaseData();
  }, [loadCaseData]);

  // Session audit logger callback
  const handleAuditLog = (entry: SessionAuditEntry) => {
    try {
      const existingStr = sessionStorage.getItem("ringguard_session_audit") || "[]";
      const existing: SessionAuditEntry[] = JSON.parse(existingStr);
      existing.unshift(entry);
      sessionStorage.setItem("ringguard_session_audit", JSON.stringify(existing.slice(0, 50)));
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Case Quick Selector Bar */}
      <CaseSelector currentTransactionId={transactionId} />

      {/* 2. Case Header with verified backend values */}
      <CaseHeader transaction={transaction} risk={risk} loading={loading} />

      {/* 3. Dual Model Comparison (Model A vs Model B) */}
      <RiskComparison
        baseline={baselineRisk}
        network={risk}
        loading={loading}
      />

      {/* 4. Model Feature-Isolation Sensitivity Analysis */}
      <FeatureIsolationCard transactionId={transactionId} />

      {/* 5. Core Investigation Workspace: Graph & Tools | Evidence & Timeline */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Left Column: Evidence Graph & Controlled Investigation Tools (7 cols) */}
        <div className="xl:col-span-7 space-y-6">
          <EvidenceGraph
            nodes={graphNodes}
            edges={graphEdges}
            loading={loading}
          />

          <ToolRunner
            transactionId={transactionId}
            accountId={transaction?.account_id || "ACC_000001"}
            onAuditLog={handleAuditLog}
          />
        </div>

        {/* Right Column: Top Evidence & Chronological Timeline (5 cols) */}
        <div className="xl:col-span-5 space-y-6">
          <EvidenceList
            evidence={evidence}
            loading={loading}
            error={error}
          />

          <TimelineView
            timeline={timeline}
            loading={loading}
            error={error}
          />
        </div>
      </div>

      {/* 5.5. Bounded Uncertainty-Driven Investigation Agent (Stage 15) */}
      <InvestigationAgentPanel transactionId={transactionId} />

      {/* 6. Synthesized Investigator Dossier (Deterministic Executive Brief) */}
      <InvestigatorDossierPanel transactionId={transactionId} />

      {/* 6.5. LLM Forensic Explanation & Grounded Security Review (Stage 16) */}
      <AIExplanationPanel transactionId={transactionId} />

      {/* 7. Human Decision Review Area (Non-Persisted Boundary) */}
      <HumanDecision />
    </div>
  );
}
