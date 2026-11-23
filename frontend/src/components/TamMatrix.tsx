"use client";

import React, { useState } from "react";
import { 
  Building2, 
  Search, 
  AlertTriangle, 
  ShieldCheck, 
  TrendingDown, 
  CheckCircle, 
  ListOrdered, 
  FileText, 
  Activity, 
  Ticket 
} from "lucide-react";
import { AccountBrief } from "@/lib/types";
import { fetchAccountBrief } from "@/lib/api";

const PRESET_ACCOUNTS = [
  { id: "ACC-3336", label: "ACC-3336 (Critical Churn / Outage)" },
  { id: "ACC-1042", label: "ACC-1042 (Billing Dispute / Underadopted)" },
  { id: "ACC-5520", label: "ACC-5520 (Healthy / Onboarding)" },
];

export default function TamMatrix({ initialAccountId }: { initialAccountId?: string }) {
  const [accountId, setAccountId] = useState(initialAccountId ?? "ACC-3336");
  const [brief, setBrief] = useState<AccountBrief | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetchBrief = async (idToFetch?: string) => {
    const targetId = idToFetch || accountId;
    if (!targetId.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await fetchAccountBrief(targetId);
      setBrief(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load account brief");
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadge = (risk: string) => {
    switch (risk?.toLowerCase()) {
      case "critical":
      case "high":
        return "border-red-500/50 bg-red-950/40 text-red-400";
      case "medium":
        return "border-amber-500/50 bg-amber-950/40 text-amber-400";
      default:
        return "border-emerald-500/50 bg-emerald-950/40 text-emerald-400";
    }
  };

  const getSeverityPill = (sev: string) => {
    switch (sev?.toLowerCase()) {
      case "critical":
        return "text-red-400 bg-red-950/30 border-red-800/60";
      case "high":
        return "text-orange-400 bg-orange-950/30 border-orange-800/60";
      case "medium":
        return "text-amber-400 bg-amber-950/30 border-amber-800/60";
      default:
        return "text-emerald-400 bg-emerald-950/30 border-emerald-800/60";
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Account Query Bar */}
      <div className="rounded-xl border border-[#222634] bg-[#11131a] p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600/10 border border-blue-500/30 text-blue-400">
              <Building2 className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-zinc-100 uppercase font-mono tracking-wide">
                Account Telemetry & Executive Briefs
              </h2>
              <p className="text-xs text-zinc-500">
                Deterministic health signal scoring paired with grounded LLM narrative synthesis.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="relative">
              <input
                type="text"
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                placeholder="Enter Account ID (e.g. ACC-3336)"
                className="w-64 rounded-lg border border-[#222634] bg-[#090a0f] pl-8 pr-3 py-2 text-xs text-zinc-200 placeholder-zinc-600 focus:border-blue-500 focus:outline-none font-mono"
              />
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-zinc-500" />
            </div>

            <button
              onClick={() => handleFetchBrief()}
              disabled={loading}
              className="rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-4 py-2 text-xs font-semibold text-white transition flex items-center space-x-1.5"
            >
              {loading ? (
                <>
                  <div className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Loading...</span>
                </>
              ) : (
                <span>Fetch Brief</span>
              )}
            </button>
          </div>
        </div>

        {/* Quick Account Switcher Chips */}
        <div className="mt-4 flex items-center space-x-2 pt-3 border-t border-[#222634]">
          <span className="text-[11px] font-mono uppercase text-zinc-500">Quick Switch:</span>
          <div className="flex flex-wrap gap-1.5">
            {PRESET_ACCOUNTS.map((preset) => (
              <button
                key={preset.id}
                onClick={() => {
                  setAccountId(preset.id);
                  handleFetchBrief(preset.id);
                }}
                className={`rounded border px-2 py-0.5 text-xs font-mono transition ${
                  accountId === preset.id
                    ? "border-blue-500/50 bg-blue-950/40 text-blue-300"
                    : "border-[#222634] bg-[#090a0f] text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-950/20 p-4 flex items-center space-x-3 text-xs text-red-300 font-mono">
          <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {brief && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Account Health Metadata & Churn Signals */}
          <div className="lg:col-span-5 space-y-4">
            {/* Account Card */}
            <div className="rounded-xl border border-[#222634] bg-[#11131a] p-5">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                    {brief.account_id}
                  </span>
                  <h3 className="text-base font-bold text-zinc-100 mt-0.5">
                    {brief.company_name || brief.account_id}
                  </h3>
                </div>
                <span className={`px-2.5 py-1 text-xs font-mono font-bold rounded-md border ${getRiskBadge(brief.risk_level)}`}>
                  {brief.risk_level?.toUpperCase()} RISK
                </span>
              </div>

              {/* Linked Ticket Summary (if present) */}
              {brief.linked_tickets_digest && (
                <div className="mt-4 grid grid-cols-3 gap-2 border-t border-[#222634] pt-4">
                  <div className="rounded-md border border-[#222634] bg-[#090a0f] p-2 text-center">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase block">Total</span>
                    <span className="text-xs font-bold text-zinc-200 font-mono">
                      {brief.linked_tickets_digest.total_tickets}
                    </span>
                  </div>
                  <div className="rounded-md border border-[#222634] bg-[#090a0f] p-2 text-center">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase block">Open</span>
                    <span className="text-xs font-bold text-zinc-200 font-mono">
                      {brief.linked_tickets_digest.open_tickets}
                    </span>
                  </div>
                  <div className="rounded-md border border-[#222634] bg-[#090a0f] p-2 text-center">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase block">P1 Escalations</span>
                    <span className="text-xs font-bold text-red-400 font-mono">
                      {brief.linked_tickets_digest.p1_count}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Churn & Health Signals Breakdown */}
            <div className="rounded-xl border border-[#222634] bg-[#11131a] p-5">
              <div className="flex items-center space-x-2 pb-3 border-b border-[#222634]">
                <Activity className="h-4 w-4 text-blue-400" />
                <h4 className="text-xs font-semibold text-zinc-200 uppercase font-mono tracking-wider">
                  Deterministic Churn Signals
                </h4>
              </div>

              <div className="mt-4 space-y-2.5">
                {brief.churn_signals?.length > 0 ? (
                  brief.churn_signals.map((signal, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-[#222634] bg-[#090a0f] p-3 text-xs"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-zinc-200">{signal.name}</span>
                        <span className={`px-2 py-0.5 text-[10px] font-mono rounded border ${getSeverityPill(signal.severity)}`}>
                          {signal.severity?.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 font-mono text-[11px] text-zinc-400">
                        <span className="text-zinc-500">Value:</span>
                        <span className="text-zinc-300 font-semibold">{String(signal.metric_value)}</span>
                      </div>
                      <p className="mt-1 text-[11px] text-zinc-500 line-clamp-2">
                        {signal.trigger_reason}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="flex items-center space-x-2 py-4 text-xs text-emerald-400 font-mono">
                    <CheckCircle className="h-4 w-4" />
                    <span>No negative churn signals triggered. Account healthy.</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Grounded Executive Brief & Action Plan */}
          <div className="lg:col-span-7 space-y-4">
            {/* Executive Summary */}
            <div className="rounded-xl border border-[#222634] bg-[#11131a] p-5">
              <div className="flex items-center space-x-2 pb-3 border-b border-[#222634]">
                <FileText className="h-4 w-4 text-blue-400" />
                <h4 className="text-xs font-semibold text-zinc-200 uppercase font-mono tracking-wider">
                  Executive Briefing (TAM Facing)
                </h4>
              </div>

              <div className="mt-4 rounded-lg bg-[#090a0f] border border-[#222634] p-4 text-xs text-zinc-300 leading-relaxed font-sans whitespace-pre-wrap">
                {brief.executive_summary}
              </div>
            </div>

            {/* Prioritized Recommended Actions */}
            <div className="rounded-xl border border-[#222634] bg-[#11131a] p-5">
              <div className="flex items-center space-x-2 pb-3 border-b border-[#222634]">
                <ListOrdered className="h-4 w-4 text-blue-400" />
                <h4 className="text-xs font-semibold text-zinc-200 uppercase font-mono tracking-wider">
                  Prioritized Action Items
                </h4>
              </div>

              <div className="mt-4 space-y-2">
                {brief.recommended_actions?.map((action, idx) => (
                  <div
                    key={idx}
                    className="flex items-start space-x-3 rounded-lg border border-[#222634] bg-[#090a0f] p-3 text-xs"
                  >
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-600/20 text-blue-400 font-mono text-[10px] font-bold border border-blue-500/30">
                      {idx + 1}
                    </span>
                    <span className="text-zinc-300 font-sans leading-relaxed pt-0.5">
                      {action}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}