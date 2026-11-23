"use client";

import { useEffect, useState } from "react";
import {
  Activity, ArrowRight, BarChart3, Building2, ChevronLeft, ChevronRight,
  CircleAlert, Clock3, RefreshCw, Search, ShieldCheck, Sparkles, Ticket, Users,
} from "lucide-react";
import { fetchAccountQueue, fetchOperationsSummary, fetchTicketQueue } from "@/lib/api";
import type { OperationsSummary, Paginated, SupportAccount, SupportTicket } from "@/lib/types";

interface Props {
  onTriage: (ticket: SupportTicket) => void;
  onAccount: (account: SupportAccount) => void;
}

const priorities = ["P1", "P2", "P3", "P4"] as const;
const statuses = ["Open", "In Progress", "Pending Customer", "Resolved", "Closed"];
const inputStyle = "w-full rounded-xl border border-white/10 bg-[#101624] px-3.5 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 outline-none transition focus:border-sky-500/70 focus:ring-2 focus:ring-sky-500/10";
const panel = "rounded-2xl border border-white/[0.08] bg-[#111825]/90 shadow-[0_12px_32px_rgba(0,0,0,.12)]";

function dateLabel(value?: string) {
  if (!value) return "Not recorded";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Not recorded"
    : date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function priorityClass(priority: string) {
  switch (priority) {
    case "P1": return "border-rose-400/20 bg-rose-400/10 text-rose-300";
    case "P2": return "border-amber-400/20 bg-amber-400/10 text-amber-300";
    case "P3": return "border-sky-400/20 bg-sky-400/10 text-sky-300";
    default: return "border-slate-400/20 bg-slate-400/10 text-slate-300";
  }
}

function riskClass(risk: string) {
  return risk === "High" ? "bg-rose-400/10 text-rose-300"
    : risk === "Medium" ? "bg-amber-400/10 text-amber-300"
    : "bg-emerald-400/10 text-emerald-300";
}

function MetricCard({ label, value, hint, icon: Icon, accent = "text-sky-300" }: {
  label: string; value: number | string; hint: string;
  icon: typeof Activity; accent?: string;
}) {
  return (
    <div className={`${panel} relative overflow-hidden p-5`}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-medium tracking-wide text-slate-400">{label}</p>
        <span className={`rounded-lg border border-white/[0.08] bg-white/[0.03] p-2 ${accent}`}>
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <p className="mt-4 text-3xl font-semibold tracking-tight text-white tabular-nums">{value}</p>
      <p className="mt-1.5 text-xs text-slate-500">{hint}</p>
    </div>
  );
}

export default function OperationsDashboard({ onTriage, onAccount }: Props) {
  const [summary, setSummary] = useState<OperationsSummary | null>(null);
  const [summaryError, setSummaryError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [view, setView] = useState<"tickets" | "accounts">("tickets");
  const [draftQuery, setDraftQuery] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [risk, setRisk] = useState("");
  const [ticketPage, setTicketPage] = useState(1);
  const [accountPage, setAccountPage] = useState(1);
  const [tickets, setTickets] = useState<Paginated<SupportTicket> | null>(null);
  const [accounts, setAccounts] = useState<Paginated<SupportAccount> | null>(null);
  const [selected, setSelected] = useState<SupportTicket | null>(null);
  const [queueError, setQueueError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetchOperationsSummary(controller.signal).then(setSummary).then(() => setSummaryError(""))
      .catch((err: Error) => { if (!controller.signal.aborted) setSummaryError(err.message); });
    return () => controller.abort();
  }, [refresh]);

  useEffect(() => {
    const timer = setTimeout(() => { setQuery(draftQuery); setTicketPage(1); setAccountPage(1); setLoading(true); }, 250);
    return () => clearTimeout(timer);
  }, [draftQuery]);


  useEffect(() => {
    const controller = new AbortController();
    const request = view === "tickets"
      ? fetchTicketQueue({ query, status, priority, page: ticketPage }, controller.signal)
          .then(setTickets)
      : fetchAccountQueue({ query, risk, page: accountPage }, controller.signal)
          .then(setAccounts);
    request.then(() => {
      if (!controller.signal.aborted) { setQueueError(""); setLoading(false); }
    }).catch((err: Error) => {
      if (!controller.signal.aborted) { setQueueError(err.message); setLoading(false); }
    });
    return () => controller.abort();
  }, [view, query, status, priority, risk, ticketPage, accountPage, refresh]);

  const trend = summary?.monthly_volume ?? [];
  const maxMonth = Math.max(1, ...trend.map((point) => point.tickets));
  const visiblePage = view === "tickets" ? ticketPage : accountPage;
  const visibleData = view === "tickets" ? tickets : accounts;
  const totalPages = visibleData?.pages ?? 1;

  function changeView(next: "tickets" | "accounts") {
    setView(next);
    setDraftQuery("");
    setQuery("");
    setSelected(null);
    setLoading(true);
  }

  return (
    <div className="mx-auto max-w-[1500px] space-y-6 px-4 py-7 sm:px-7 lg:px-10">
      <section className="relative overflow-hidden rounded-3xl border border-sky-400/10 bg-gradient-to-br from-[#16263d] via-[#101a2c] to-[#111825] px-6 py-7 sm:px-9 sm:py-9">
        <div className="pointer-events-none absolute -right-20 -top-28 h-80 w-80 rounded-full bg-sky-500/10 blur-3xl" />
        <div className="relative flex flex-wrap items-start justify-between gap-5">
          <div className="max-w-2xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-sky-400/20 bg-sky-400/10 px-3 py-1 text-[11px] font-medium tracking-wide text-sky-200">
              <span className="h-1.5 w-1.5 rounded-full bg-sky-400" />
              SUPPORT OPERATIONS / DATASET EXPLORER
            </div>
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              Your support queue, in focus.
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
              Explore incoming issues, understand what needs attention, and move from ticket details
              to an evidence-informed AI triage. All numbers below come from the bundled sample dataset.
            </p>
          </div>
          <button onClick={() => { setLoading(true); setRefresh((n) => n + 1); }}
            className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-xs font-medium text-white hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-sky-400">
            <RefreshCw className="h-3.5 w-3.5" /> Refresh snapshot
          </button>
        </div>
      </section>

      {summaryError && (
        <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-100">
          <span><CircleAlert className="mr-2 inline h-4 w-4" />Couldn&apos;t load the API: {summaryError}. Start the FastAPI server on port 8000.</span>
          <button className="underline" onClick={() => setRefresh((n) => n + 1)}>Retry</button>
        </div>
      )}

      <section aria-label="Support snapshot" className="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4">
        <MetricCard label="Total tickets" value={summary?.total_tickets ?? "—"} icon={Ticket} hint="Historical sample records" />
        <MetricCard label="Active queue" value={summary?.active_tickets ?? "—"} icon={Activity} hint="Open, in progress or waiting" accent="text-violet-300" />
        <MetricCard label="P1 needing attention" value={summary?.critical_active ?? "—"} icon={CircleAlert} hint="Unresolved critical tickets" accent="text-rose-300" />
        <MetricCard label="High-risk accounts" value={summary?.high_risk_accounts ?? "—"} icon={Users} hint={`From ${summary?.total_accounts ?? "—"} sample accounts`} accent="text-amber-300" />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-[1.45fr_1fr]">
        <div className={`${panel} p-5 sm:p-6`}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                <BarChart3 className="h-4 w-4 text-sky-300" /> Ticket volume
              </h2>
              <p className="mt-1 text-xs text-slate-500">Tickets created per month, across available records</p>
            </div>
            <span className="rounded-md bg-white/5 px-2.5 py-1 text-[10px] uppercase tracking-wide text-slate-400">Historical</span>
          </div>
          <div className="mt-6 flex h-40 items-end gap-2 border-b border-white/10 pb-1 sm:gap-4">
            {trend.length ? trend.map(({ month, tickets: count }) => (
              <div key={month} className="group flex h-full min-w-0 flex-1 flex-col items-center justify-end gap-2">
                <div className="relative flex h-[112px] w-full max-w-12 items-end justify-center">
                  <div title={`${count} tickets in ${month}`} style={{ height: `${Math.max(5, count / maxMonth * 100)}%` }}
                    className="w-full rounded-t-md bg-gradient-to-t from-sky-700 to-cyan-400/90 transition-colors group-hover:from-sky-500 group-hover:to-cyan-300" />
                </div>
                <span className="text-[10px] text-slate-500">{month.slice(5)}</span>
              </div>
            )) : <p className="m-auto text-xs text-slate-500">Start the API to view trends.</p>}
          </div>
          <p className="mt-3 text-[11px] text-slate-500">Month labels refer to the sample dataset&apos;s creation timestamps.</p>
        </div>

        <div className={`${panel} p-5 sm:p-6`}>
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-100">
            <ShieldCheck className="h-4 w-4 text-violet-300" /> Priority distribution
          </h2>
          <p className="mt-1 text-xs text-slate-500">All historical tickets, including resolved</p>
          <div className="mt-6 space-y-4">
            {priorities.map((p) => {
              const count = summary?.priority_counts?.[p] || 0;
              return (
                <div key={p} className="flex items-center gap-3">
                  <span className={`w-10 rounded-md border px-1.5 py-0.5 text-center text-[11px] font-semibold ${priorityClass(p)}`}>{p}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/5">
                    <div className="h-full rounded-full bg-gradient-to-r from-sky-600 to-cyan-400"
                      style={{ width: `${summary?.total_tickets ? count / summary.total_tickets * 100 : 0}%` }} />
                  </div>
                  <span className="w-8 text-right text-xs tabular-nums text-slate-300">{summary ? count : "—"}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className={`${panel} overflow-hidden`}>
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-white/[0.08] px-5 py-5 sm:px-6">
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-white">Workspace</h2>
            <p className="mt-1 text-xs text-slate-400">Review individual records before moving to AI analysis.</p>
          </div>
          <div className="flex gap-1 rounded-xl border border-white/10 bg-[#0b1220] p-1" role="group" aria-label="Workspace view">
            <button onClick={() => changeView("tickets")} aria-pressed={view === "tickets"}
              className={`rounded-lg px-4 py-2 text-xs font-medium transition ${view === "tickets" ? "bg-sky-600 text-white" : "text-slate-400 hover:text-white"}`}>
              Tickets
            </button>
            <button onClick={() => changeView("accounts")} aria-pressed={view === "accounts"}
              className={`rounded-lg px-4 py-2 text-xs font-medium transition ${view === "accounts" ? "bg-sky-600 text-white" : "text-slate-400 hover:text-white"}`}>
              Accounts
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 border-b border-white/[0.08] px-5 py-4 sm:px-6">
          <label className="relative min-w-[190px] flex-1">
            <span className="sr-only">Search {view}</span>
            <Search className="pointer-events-none absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
            <input value={draftQuery} onChange={(e) => setDraftQuery(e.target.value)}
              placeholder={view === "tickets" ? "Search by ticket, company or subject" : "Search company, account or TAM"}
              className={`${inputStyle} pl-10`} />
          </label>
          {view === "tickets" ? (
            <>
              <label className="min-w-[155px]"><span className="sr-only">Filter by status</span>
                <select className={inputStyle} value={status} onChange={(e) => { setStatus(e.target.value); setTicketPage(1); setLoading(true); }}>
                  <option value="">All statuses</option>
                  {statuses.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              <label className="min-w-[130px]"><span className="sr-only">Filter by priority</span>
                <select className={inputStyle} value={priority} onChange={(e) => { setPriority(e.target.value); setTicketPage(1); setLoading(true); }}>
                  <option value="">All priorities</option>
                  {priorities.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
            </>
          ) : (
            <label className="min-w-[140px]"><span className="sr-only">Filter by risk</span>
              <select className={inputStyle} value={risk} onChange={(e) => { setRisk(e.target.value); setAccountPage(1); setLoading(true); }}>
                <option value="">All risk levels</option>
                {["High", "Medium", "Low"].map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
          )}
        </div>

        <div className="grid min-h-[420px] grid-cols-1 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="min-w-0 border-r border-white/[0.08]">
            {queueError ? (
              <div role="alert" className="p-8 text-sm text-rose-300">
                Unable to load records: {queueError}
                <button className="ml-3 underline" onClick={() => setRefresh((n) => n + 1)}>Retry</button>
              </div>
            ) : loading && !visibleData ? (
              <div className="p-8 text-sm text-slate-400" role="status">Loading records...</div>
            ) : view === "tickets" ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[680px] text-left">
                  <thead className="bg-white/[0.025] text-[11px] uppercase tracking-wide text-slate-500">
                    <tr><th className="px-5 py-3 font-medium">Ticket</th><th className="px-4 py-3 font-medium">Priority</th>
                      <th className="px-4 py-3 font-medium">Status</th><th className="px-4 py-3 font-medium">Updated</th></tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.06]">
                    {tickets?.items.map((ticket) => (
                      <tr key={ticket.ticket_id} className={`transition-colors hover:bg-white/[0.04] ${selected?.ticket_id === ticket.ticket_id ? "bg-sky-500/[0.07]" : ""}`}>
                        <td className="px-5 py-3.5">
                          <button className="block max-w-[360px] text-left focus-visible:outline-2 focus-visible:outline-sky-400" onClick={() => setSelected(ticket)}>
                            <span className="block text-[11px] font-medium text-sky-300">{ticket.ticket_id} · {ticket.company}</span>
                            <span className="mt-1 block truncate text-sm font-medium text-slate-100">{ticket.subject}</span>
                          </button>
                        </td>
                        <td className="px-4 py-3.5"><span className={`rounded-md border px-2 py-1 text-xs font-semibold ${priorityClass(ticket.urgency)}`}>{ticket.urgency}</span></td>
                        <td className="px-4 py-3.5 text-xs text-slate-300">{ticket.status}</td>
                        <td className="whitespace-nowrap px-4 py-3.5 text-xs text-slate-400">{dateLabel(ticket.updated_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {tickets?.items.length === 0 && <p className="p-10 text-center text-sm text-slate-400">No tickets match these filters.</p>}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[620px] text-left">
                  <thead className="bg-white/[0.025] text-[11px] uppercase tracking-wide text-slate-500">
                    <tr><th className="px-5 py-3 font-medium">Account</th><th className="px-4 py-3 font-medium">Risk</th>
                      <th className="px-4 py-3 font-medium">Open cases</th><th className="px-4 py-3 font-medium">Owner</th></tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.06]">
                    {accounts?.items.map((account) => (
                      <tr key={account.account_id} className="hover:bg-white/[0.04]">
                        <td className="px-5 py-3.5">
                          <button onClick={() => onAccount(account)} className="text-left focus-visible:outline-2 focus-visible:outline-sky-400">
                            <span className="block text-sm font-medium text-slate-100">{account.company}</span>
                            <span className="mt-1 block text-[11px] text-sky-300">{account.account_id}</span>
                          </button>
                        </td>
                        <td className="px-4 py-3.5"><span className={`rounded-md px-2 py-1 text-xs font-medium ${riskClass(account.risk_level)}`}>{account.risk_level}</span></td>
                        <td className="px-4 py-3.5 text-xs tabular-nums text-slate-300">{account.open_tickets}</td>
                        <td className="px-4 py-3.5 text-xs text-slate-400">{account.tam}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {accounts?.items.length === 0 && <p className="p-10 text-center text-sm text-slate-400">No accounts match these filters.</p>}
              </div>
            )}

            <div className="flex items-center justify-between gap-3 border-t border-white/[0.08] px-5 py-3 text-xs text-slate-400">
              <span>{loading ? "Updating..." : `${visibleData?.total ?? 0} records`}</span>
              <div className="flex items-center gap-3">
                <button aria-label="Previous page" disabled={visiblePage <= 1 || loading} className="rounded-md p-1 hover:bg-white/10 disabled:opacity-30"
                  onClick={() => { setLoading(true); if (view === "tickets") setTicketPage((p) => p - 1); else setAccountPage((p) => p - 1); }}>
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span>Page {visiblePage} of {totalPages}</span>
                <button aria-label="Next page" disabled={visiblePage >= totalPages || loading} className="rounded-md p-1 hover:bg-white/10 disabled:opacity-30"
                  onClick={() => { setLoading(true); if (view === "tickets") setTicketPage((p) => p + 1); else setAccountPage((p) => p + 1); }}>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          <aside className="bg-[#0c1320]/80 p-5 sm:p-6" aria-label={view === "tickets" ? "Ticket details" : "Account information"}>
            {view === "tickets" && selected ? (
              <div className="space-y-5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-xs font-semibold text-sky-300">{selected.ticket_id}</span>
                    <h3 className="mt-2 text-lg font-semibold leading-6 text-white">{selected.subject}</h3>
                  </div>
                  <span className={`shrink-0 rounded-md border px-2 py-1 text-xs font-semibold ${priorityClass(selected.urgency)}`}>{selected.urgency}</span>
                </div>
                <p className="whitespace-pre-wrap break-words rounded-xl border border-white/[0.07] bg-white/[0.025] p-3 text-xs leading-5 text-slate-300">
                  {selected.body}
                </p>
                <dl className="grid grid-cols-2 gap-x-3 gap-y-4 text-xs">
                  {[
                    ["Company", selected.company], ["Account", selected.account_id || "Unlinked"],
                    ["Product", selected.product], ["Category", selected.category],
                    ["Status", selected.status], ["Assigned to", selected.assigned_agent || "Unassigned"],
                    ["Channel", selected.channel], ["Created", dateLabel(selected.created_at)],
                  ].map(([label, value]) => <div key={label}>
                    <dt className="mb-1 text-slate-500">{label}</dt><dd className="break-words font-medium text-slate-200">{value}</dd>
                  </div>)}
                </dl>
                <button onClick={() => onTriage(selected)}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-sky-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-400">
                  <Sparkles className="h-4 w-4" /> Analyze with AI <ArrowRight className="h-4 w-4" />
                </button>
                <p className="text-[11px] leading-5 text-slate-500">Opens the existing triage studio with this ticket prefilled. No changes are made to the sample dataset.</p>
              </div>
            ) : (
              <div className="flex h-full min-h-[300px] flex-col items-center justify-center text-center">
                <div className="rounded-2xl border border-sky-400/15 bg-sky-400/10 p-4 text-sky-300">
                  {view === "tickets" ? <Ticket className="h-7 w-7" /> : <Building2 className="h-7 w-7" />}
                </div>
                <h3 className="mt-5 text-base font-semibold text-slate-100">
                  {view === "tickets" ? "Select a ticket" : "Explore account health"}
                </h3>
                <p className="mt-2 max-w-[240px] text-xs leading-6 text-slate-400">
                  {view === "tickets"
                    ? "Choose any ticket from the queue to view its details and run AI triage."
                    : "Filter by risk level, then choose an account to open its health brief."}
                </p>
                <div className="mt-5 flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.025] px-3 py-1.5 text-[11px] text-slate-400">
                  <Clock3 className="h-3.5 w-3.5" /> Read-only sample data
                </div>
              </div>
            )}
          </aside>
        </div>
      </section>
      <footer className="flex items-start gap-2 text-xs leading-5 text-slate-500">
        <CircleAlert className="mt-0.5 h-4 w-4 shrink-0" />
        This is a development workspace using 500 synthetic tickets and 50 synthetic accounts.
        Priority labels and account risk are derived from sample data, not live customer telemetry.
      </footer>
    </div>
  );
}
