"use client";

import React, { useState } from "react";
import { 
  Send, 
  Sparkles, 
  BookOpen, 
  AlertCircle, 
  ShieldAlert, 
  Copy, 
  Check, 
  Cpu 
} from "lucide-react";
import { TicketInput } from "@/lib/types";
import { submitTriage } from "@/lib/api";

const PRESET_TICKETS: { label: string; data: TicketInput }[] = [
  {
    label: "P1 Data Loss / Crash",
    data: {
      account_id: "ACC-3336",
      subject: "URGENT: Production database replication failure after upgrade",
      body: "Our primary DB cluster dropped replica sync immediately following the v4.12 update. Several worker nodes are throwing unhandled write lock exceptions and customer records are desynchronized. We need engineering escalation immediately.",
    },
  },
  {
    label: "Billing / Refund Dispute",
    data: {
      account_id: "ACC-1042",
      subject: "Overcharged on Enterprise seat true-up invoice #INV-9921",
      body: "We were billed for 45 active seats on our latest invoice, but our admin console only shows 28 provisioned users. Please adjust this charge and issue a revised billing statement before net-30 terms expire.",
    },
  },
  {
    label: "How-To / KB Match",
    data: {
      account_id: "ACC-5520",
      subject: "Configuring SAML SSO with Okta IdP metadata",
      body: "We are migrating to Okta for workforce authentication. Where do we paste our ACS URL and download the SP metadata XML file inside the workspace admin dashboard?",
    },
  },
];

export default function TriageStudio({ initialTicket }: { initialTicket?: TicketInput }) {
  const [ticket, setTicket] = useState<TicketInput>(initialTicket ?? PRESET_TICKETS[0].data);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleTriage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!ticket.subject.trim() || !ticket.body.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await submitTriage(ticket);
      console.log("Triage Response Data:", data);
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to run triage pipeline");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Safe property extraction
  const assignedTeam = result?.routing?.assigned_team || result?.assigned_team || result?.team || "Tier 1 Support";
  const priority = result?.routing?.priority || result?.priority || result?.classification?.urgency || "P3";
  const routingReason = result?.routing?.routing_reason || result?.routing_reason || result?.reason || "Matched standard triage rules";
  const category = result?.classification?.category || result?.category || "General";
  const productArea = result?.classification?.product_area || result?.product_area || "Platform";
  const urgency = result?.classification?.urgency || result?.urgency || priority;
  
  const draftReply = 
    typeof result?.draft_response === "string" 
      ? result.draft_response 
      : result?.draft_response?.reply_text || result?.reply_text || result?.draft_reply || "No draft reply generated.";
  
  const hallucinationRisk = 
    result?.draft_response?.hallucination_risk || result?.hallucination_risk || "low";
  
  const retrievedChunks = 
    result?.grounding?.retrieved_chunks || result?.retrieved_chunks || result?.matched_chunks || [];
  
  const citations = 
    result?.draft_response?.citations || result?.citations || result?.grounding?.matched_articles || [];

  const getPriorityBadge = (p: string) => {
    switch (p) {
      case "P1":
        return "border-red-500/50 bg-red-950/40 text-red-400";
      case "P2":
        return "border-amber-500/50 bg-amber-950/40 text-amber-400";
      case "P3":
        return "border-blue-500/50 bg-blue-950/40 text-blue-400";
      default:
        return "border-zinc-700 bg-zinc-800 text-zinc-300";
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 max-w-7xl mx-auto">
      {/* Left Column: Ticket Ingestion */}
      <div className="lg:col-span-5 flex flex-col space-y-4">
        <div className="rounded-xl border border-[#222634] bg-[#11131a] p-5 shadow-lg">
          <div className="flex items-center justify-between pb-3 border-b border-[#222634]">
            <div className="flex items-center space-x-2">
              <Cpu className="h-4 w-4 text-blue-400" />
              <h2 className="text-sm font-semibold tracking-wide text-zinc-100 uppercase font-mono">
                Ticket Ingestion
              </h2>
            </div>
            <span className="text-[11px] font-mono text-zinc-500">POST /triage</span>
          </div>

          <div className="mt-4">
            <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-500 block mb-2">
              Load Preset Scenarios:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {PRESET_TICKETS.map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setTicket(preset.data);
                    setResult(null);
                    setError(null);
                  }}
                  className="rounded-md border border-[#222634] bg-[#090a0f] px-2.5 py-1 text-xs text-zinc-300 hover:border-blue-500/40 hover:text-blue-400 transition"
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleTriage} className="mt-4 space-y-3">
            <div>
              <label className="block text-[11px] font-mono uppercase text-zinc-400 mb-1">
                Account Identifier (Optional)
              </label>
              <input
                type="text"
                value={ticket.account_id || ""}
                onChange={(e) => setTicket({ ...ticket, account_id: e.target.value })}
                placeholder="e.g. ACC-3336"
                className="w-full rounded-md border border-[#222634] bg-[#090a0f] px-3 py-2 text-xs text-zinc-200 placeholder-zinc-600 focus:border-blue-500 focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="block text-[11px] font-mono uppercase text-zinc-400 mb-1">
                Subject Line
              </label>
              <input
                type="text"
                required
                value={ticket.subject}
                onChange={(e) => setTicket({ ...ticket, subject: e.target.value })}
                placeholder="Brief summary of the issue"
                className="w-full rounded-md border border-[#222634] bg-[#090a0f] px-3 py-2 text-xs text-zinc-200 placeholder-zinc-600 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-mono uppercase text-zinc-400 mb-1">
                Raw Ticket Body
              </label>
              <textarea
                required
                rows={7}
                value={ticket.body}
                onChange={(e) => setTicket({ ...ticket, body: e.target.value })}
                placeholder="Paste full ticket transcript..."
                className="w-full rounded-md border border-[#222634] bg-[#090a0f] px-3 py-2 text-xs text-zinc-200 placeholder-zinc-600 focus:border-blue-500 focus:outline-none resize-none font-mono leading-relaxed"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-4 py-2.5 text-xs font-semibold text-white shadow-md transition"
            >
              {loading ? (
                <>
                  <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Executing Pipeline...</span>
                </>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" />
                  <span>Run Triage Pipeline</span>
                </>
              )}
            </button>
          </form>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-950/20 p-3.5 flex items-start space-x-2.5 text-xs text-red-300">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold block">Execution Error</span>
              <span className="font-mono text-[11px] opacity-90">{error}</span>
            </div>
          </div>
        )}
      </div>

      {/* Right Column: Pipeline Execution Telemetry & Results */}
      <div className="lg:col-span-7 flex flex-col space-y-4">
        {!result && !loading && (
          <div className="h-full min-h-[440px] flex flex-col items-center justify-center rounded-xl border border-dashed border-[#222634] bg-[#11131a]/50 p-8 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500 mb-3">
              <Sparkles className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-medium text-zinc-300">Pipeline Awaiting Execution</h3>
            <p className="mt-1 text-xs text-zinc-500 max-w-sm">
              Submit a ticket on the left or select a preset to trigger MiniLM vector search, Groq classification, and grounded response drafting.
            </p>
          </div>
        )}

        {loading && (
          <div className="h-full min-h-[440px] flex flex-col items-center justify-center rounded-xl border border-[#222634] bg-[#11131a] p-8 text-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent mb-4" />
            <span className="text-xs font-mono text-zinc-300">
              1. Classifying intent · 2. FAISS chunk retrieval · 3. Hardening draft
            </span>
          </div>
        )}

        {result && (
          <div className="space-y-4">
            {/* Top Metadata Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="rounded-lg border border-[#222634] bg-[#11131a] p-3">
                <span className="text-[10px] font-mono uppercase text-zinc-500">Routing Decision</span>
                <div className="mt-1 flex items-center justify-between">
                  <span className="text-sm font-bold text-zinc-100 font-mono">
                    {assignedTeam}
                  </span>
                  <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${getPriorityBadge(priority)}`}>
                    {priority}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-zinc-400 line-clamp-2">
                  {routingReason}
                </p>
              </div>

              <div className="rounded-lg border border-[#222634] bg-[#11131a] p-3">
                <span className="text-[10px] font-mono uppercase text-zinc-500">Classification</span>
                <div className="mt-1">
                  <span className="text-sm font-semibold text-zinc-200">
                    {category}
                  </span>
                  <div className="mt-1 flex items-center space-x-2 text-[11px] text-zinc-400">
                    <span>Area: {productArea}</span>
                    <span>·</span>
                    <span>Urgency: {urgency}</span>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-[#222634] bg-[#11131a] p-3">
                <span className="text-[10px] font-mono uppercase text-zinc-500">Hallucination Risk</span>
                <div className="mt-1 flex items-center space-x-1.5">
                  <ShieldAlert className="h-4 w-4 text-emerald-400" />
                  <span className="text-sm font-bold text-emerald-400 font-mono">
                    {String(hallucinationRisk).toUpperCase()}
                  </span>
                </div>
                <div className="mt-1 text-[11px] text-zinc-400">
                  Grounded in FAISS excerpts
                </div>
              </div>
            </div>

            {/* Grounded First Response Draft */}
            <div className="rounded-xl border border-[#222634] bg-[#11131a] p-4 shadow-sm">
              <div className="flex items-center justify-between pb-2.5 border-b border-[#222634]">
                <div className="flex items-center space-x-2">
                  <Sparkles className="h-4 w-4 text-blue-400" />
                  <h3 className="text-xs font-semibold text-zinc-100 uppercase font-mono tracking-wider">
                    Grounded Draft Response (respond_v2)
                  </h3>
                </div>
                <button
                  onClick={() => handleCopy(draftReply)}
                  className="flex items-center space-x-1 rounded border border-[#222634] bg-[#090a0f] px-2 py-1 text-[11px] font-mono text-zinc-400 hover:text-zinc-200 hover:border-zinc-700 transition"
                >
                  {copied ? (
                    <>
                      <Check className="h-3 w-3 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      <span>Copy Reply</span>
                    </>
                  )}
                </button>
              </div>

              <div className="mt-3 rounded-lg bg-[#090a0f] border border-[#222634] p-3.5 text-xs text-zinc-300 leading-relaxed font-sans whitespace-pre-wrap">
                {draftReply}
              </div>

              {citations?.length > 0 && (
                <div className="mt-3 flex items-center space-x-2 text-[11px] text-zinc-400 font-mono">
                  <span className="text-zinc-500">Citations:</span>
                  <div className="flex flex-wrap gap-1">
                    {citations.map((cite: string, i: number) => (
                      <span
                        key={i}
                        className="rounded border border-blue-900/50 bg-blue-950/30 px-1.5 py-0.5 text-blue-300"
                      >
                        {cite}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Semantic Vector Retrieval Breakdown */}
            <div className="rounded-xl border border-[#222634] bg-[#11131a] p-4">
              <div className="flex items-center space-x-2 pb-2.5 border-b border-[#222634]">
                <BookOpen className="h-4 w-4 text-zinc-400" />
                <h3 className="text-xs font-semibold text-zinc-200 uppercase font-mono tracking-wider">
                  FAISS Knowledge Base Retrieval
                </h3>
              </div>

              <div className="mt-3 space-y-2">
                {retrievedChunks.length > 0 ? (
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  retrievedChunks.map((chunk: any, idx: number) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-[#222634] bg-[#090a0f] p-3 text-xs"
                    >
                      <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400 mb-1.5">
                        <span className="font-semibold text-blue-400">
                          {chunk.doc_id || chunk.article_id || `Chunk #${idx + 1}`}
                        </span>
                        <span className="text-zinc-500">
                          Score: {typeof chunk.similarity_score === "number" ? chunk.similarity_score.toFixed(3) : "Matched"}
                        </span>
                      </div>
                      <span className="text-zinc-200 font-medium block text-[11px]">
                        {chunk.heading || chunk.title || "Knowledge Base Section"}
                      </span>
                      <p className="mt-1 text-zinc-400 font-mono text-[11px] line-clamp-2">
                        {chunk.content || chunk.text || JSON.stringify(chunk)}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-zinc-500 font-mono py-2">
                    Direct classification executed. No auxiliary retrieval chunks required.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}