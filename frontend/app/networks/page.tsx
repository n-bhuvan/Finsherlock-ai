"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { Node, Edge } from "@xyflow/react";
import {
  Share2,
  Filter,
  RefreshCw,
  Smartphone,
  Wifi,
  Users,
  ShieldAlert,
  Database,
} from "lucide-react";
import {
  investigateAccount,
  investigateSharedDevices,
  investigateSharedIPs,
  investigateCommonBeneficiaries,
  investigateRelatedAccounts,
  investigateTransactionFundFlow,
} from "@/lib/api";
import { EvidenceGraph } from "@/components/graph/EvidenceGraph";
import { GraphNodeData } from "@/types/graph";

const SELECTABLE_CASES = [
  { id: "ACC_000001", txnId: "TXN_00000646", label: "ACC_000001 (Hero Abuse Ring)" },
  { id: "ACC_000002", txnId: "TXN_00000679", label: "ACC_000002 (Coordinated Peer)" },
  { id: "ACC_000118", txnId: "TXN_00000001", label: "ACC_000118 (Clean Lookalike)" },
  { id: "ACC_000230", txnId: "TXN_00000500", label: "ACC_000230 (Standard Merchant)" },
];

export default function NetworksPage() {
  const [selectedAccount, setSelectedAccount] = useState("ACC_000001");
  const [loading, setLoading] = useState(true);

  // Filter toggles
  const [showDevices, setShowDevices] = useState(true);
  const [showIps, setShowIps] = useState(true);
  const [showBeneficiaries, setShowBeneficiaries] = useState(true);

  // Raw fetched data
  const [rawDevices, setRawDevices] = useState<any[]>([]);
  const [rawIps, setRawIps] = useState<any[]>([]);
  const [rawBeneficiaries, setRawBeneficiaries] = useState<any[]>([]);
  const [rawRelated, setRawRelated] = useState<any[]>([]);

  const loadNetworkData = useCallback(async () => {
    setLoading(true);

    const [devRes, ipRes, benRes, relRes] = await Promise.all([
      investigateSharedDevices(selectedAccount),
      investigateSharedIPs(selectedAccount),
      investigateCommonBeneficiaries(selectedAccount),
      investigateRelatedAccounts(selectedAccount, 20),
    ]);

    setRawDevices(devRes.data?.result || []);
    setRawIps(ipRes.data?.result || []);
    setRawBeneficiaries(benRes.data?.result || []);
    setRawRelated(relRes.data?.result || []);

    setLoading(false);
  }, [selectedAccount]);

  useEffect(() => {
    loadNetworkData();
  }, [loadNetworkData]);

  // Construct filtered graph nodes & edges strictly from verified data
  const { nodes, edges } = useMemo(() => {
    const n: Node<GraphNodeData>[] = [];
    const e: Edge[] = [];

    // 1. Center Target Account
    n.push({
      id: selectedAccount,
      type: "entityNode",
      position: { x: 300, y: 190 },
      data: {
        id: selectedAccount,
        label: selectedAccount,
        type: "account",
        sublabel: "Investigation Focus",
        isFocus: true,
        metadata: {
          "Entity Type": "Account",
          "Role": "Investigation Origin",
        },
      },
    });

    // 2. Devices
    if (showDevices) {
      rawDevices.forEach((dev, idx) => {
        const devId = dev.device_id;
        n.push({
          id: devId,
          type: "entityNode",
          position: { x: 120 + idx * 180, y: 30 },
          data: {
            id: devId,
            label: devId,
            type: "device",
            sublabel: `${dev.device_os} (${dev.device_type})`,
            metadata: {
              "Type": dev.device_type,
              "OS": dev.device_os,
              "Co-using Accounts": dev.co_using_accounts.join(", "),
            },
          },
        });

        e.push({
          id: `edge-${selectedAccount}-${devId}`,
          source: selectedAccount,
          target: devId,
          label: "USED_DEVICE",
        });

        // Add connected peer accounts
        dev.co_using_accounts.forEach((peerAcc: string, pIdx: number) => {
          if (peerAcc !== selectedAccount && !n.some((x) => x.id === peerAcc)) {
            n.push({
              id: peerAcc,
              type: "entityNode",
              position: { x: 380 + pIdx * 140, y: 30 },
              data: {
                id: peerAcc,
                label: peerAcc,
                type: "account",
                sublabel: "Shared Device Co-User",
                metadata: { "Connected Device": devId },
              },
            });
            e.push({
              id: `edge-${peerAcc}-${devId}`,
              source: peerAcc,
              target: devId,
              label: "CO_LINKED",
            });
          }
        });
      });
    }

    // 3. IPs
    if (showIps) {
      rawIps.forEach((ip, idx) => {
        const ipId = ip.ip_id;
        n.push({
          id: ipId,
          type: "entityNode",
          position: { x: 540 + idx * 160, y: 190 },
          data: {
            id: ipId,
            label: ipId,
            type: "ip",
            sublabel: `${ip.ip_address} (${ip.country})`,
            metadata: {
              "IP Address": ip.ip_address,
              "Type": ip.ip_type,
              "Country": ip.country,
              "ASN/Org": ip.asn_org,
            },
          },
        });

        e.push({
          id: `edge-${selectedAccount}-${ipId}`,
          source: selectedAccount,
          target: ipId,
          label: "SHARED_IP",
        });
      });
    }

    // 4. Beneficiaries
    if (showBeneficiaries) {
      rawBeneficiaries.forEach((ben, idx) => {
        const benId = ben.beneficiary_id;
        n.push({
          id: benId,
          type: "entityNode",
          position: { x: 220 + idx * 200, y: 360 },
          data: {
            id: benId,
            label: benId,
            type: "beneficiary",
            sublabel: ben.beneficiary_type,
            metadata: {
              "Type": ben.beneficiary_type,
              "Bank Prefix": ben.bank_ifsc_prefix,
              "Co-sending Accounts": ben.co_sending_accounts.join(", "),
            },
          },
        });

        e.push({
          id: `edge-${selectedAccount}-${benId}`,
          source: selectedAccount,
          target: benId,
          label: "SENT_FUNDS",
        });

        // Add co-sending accounts
        ben.co_sending_accounts.forEach((coAcc: string, cIdx: number) => {
          if (coAcc !== selectedAccount && !n.some((x) => x.id === coAcc)) {
            n.push({
              id: coAcc,
              type: "entityNode",
              position: { x: 480 + cIdx * 140, y: 360 },
              data: {
                id: coAcc,
                label: coAcc,
                type: "account",
                sublabel: "Common Payee Sender",
                metadata: { "Common Beneficiary": benId },
              },
            });
            e.push({
              id: `edge-${coAcc}-${benId}`,
              source: coAcc,
              target: benId,
              label: "CO_SENT",
            });
          }
        });
      });
    }

    return { nodes: n, edges: e };
  }, [selectedAccount, rawDevices, rawIps, rawBeneficiaries, showDevices, showIps, showBeneficiaries]);

  return (
    <div className="space-y-6 select-none font-mono text-xs">
      {/* 1. Header & Case Selector */}
      <section className="p-5 rounded-xl bg-[#0b151b] border border-[#142a32] shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#142a32] pb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Share2 className="w-4 h-4 text-cyan-400" />
              <h1 className="text-lg font-bold text-white font-sans tracking-wide">
                Case-Centric Network Explorer
              </h1>
            </div>
            <p className="text-slate-400 text-xs font-sans">
              Explores verified relationship topology centered on a target account. Grounded exclusively in live database records:
            </p>
          </div>

          {/* Quick Account Switcher */}
          <div className="flex items-center gap-2">
            <select
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              className="bg-[#081216] border border-[#142a32] rounded-lg px-3 py-1.5 text-xs text-cyan-300 font-mono focus:outline-none focus:border-cyan-500 cursor-pointer"
            >
              {SELECTABLE_CASES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>

            <button
              onClick={loadNetworkData}
              disabled={loading}
              className="p-1.5 rounded-lg bg-[#081216] hover:bg-[#11242b] border border-[#142a32] text-slate-300 hover:text-white transition cursor-pointer"
              title="Refresh network data"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Filter Toggles & Statistics */}
        <div className="flex flex-wrap items-center justify-between gap-4 text-[11px]">
          <div className="flex items-center gap-2">
            <span className="text-slate-500 flex items-center gap-1">
              <Filter className="w-3 h-3 text-cyan-400" /> Layer Filters:
            </span>

            <button
              onClick={() => setShowDevices(!showDevices)}
              className={`px-2.5 py-1 rounded-md border transition cursor-pointer flex items-center gap-1.5 ${
                showDevices
                  ? "bg-emerald-950/70 border-emerald-600/60 text-emerald-300"
                  : "bg-[#081216] border-[#142a32] text-slate-500"
              }`}
            >
              <Smartphone className="w-3 h-3" />
              <span>Devices ({rawDevices.length})</span>
            </button>

            <button
              onClick={() => setShowIps(!showIps)}
              className={`px-2.5 py-1 rounded-md border transition cursor-pointer flex items-center gap-1.5 ${
                showIps
                  ? "bg-amber-950/70 border-amber-600/60 text-amber-300"
                  : "bg-[#081216] border-[#142a32] text-slate-500"
              }`}
            >
              <Wifi className="w-3 h-3" />
              <span>IPs ({rawIps.length})</span>
            </button>

            <button
              onClick={() => setShowBeneficiaries(!showBeneficiaries)}
              className={`px-2.5 py-1 rounded-md border transition cursor-pointer flex items-center gap-1.5 ${
                showBeneficiaries
                  ? "bg-purple-950/70 border-purple-600/60 text-purple-300"
                  : "bg-[#081216] border-[#142a32] text-slate-500"
              }`}
            >
              <Users className="w-3 h-3" />
              <span>Beneficiaries ({rawBeneficiaries.length})</span>
            </button>
          </div>

          <div className="text-slate-400 font-mono text-[10px] flex items-center gap-3">
            <span>Discovered Peer Accounts: <strong className="text-cyan-300">{rawRelated.length}</strong></span>
            <span>Total Nodes: <strong className="text-white">{nodes.length}</strong></span>
          </div>
        </div>
      </section>

      {/* 2. Interactive Graph Canvas */}
      <EvidenceGraph nodes={nodes} edges={edges} loading={loading} />

      {/* 3. Data Integrity & Boundary Notice */}
      <div className="p-4 rounded-xl bg-[#0b151b] border border-[#142a32] text-xs text-slate-400 font-sans space-y-1 leading-relaxed">
        <div className="flex items-center gap-1.5 text-cyan-400 font-bold font-mono text-xs">
          <Database className="w-3.5 h-3.5" />
          <span>Factual Grounding Guarantee</span>
        </div>
        <p className="text-[11px] text-slate-400">
          This network view is strictly derived from real transactions and shared endpoint identifiers stored in the PostgreSQL database. Node relationships correspond to direct foreign keys or co-usage. Beneficiary links reflect payment destinations and are never represented as unsupported account-to-account transfers.
        </p>
      </div>
    </div>
  );
}
