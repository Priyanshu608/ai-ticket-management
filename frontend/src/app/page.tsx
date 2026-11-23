"use client";

import { useState } from "react";
import Navbar, { type WorkspaceTab } from "@/components/Navbar";
import OperationsDashboard from "@/components/OperationsDashboard";
import TriageStudio from "@/components/TriageStudio";
import TamMatrix from "@/components/TamMatrix";
import EvalBenchmarks from "@/components/EvalBenchmarks";
import type { SupportAccount, SupportTicket, TicketInput } from "@/lib/types";

export default function Home() {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("overview");
  const [triageTicket, setTriageTicket] = useState<TicketInput | undefined>();
  const [triageKey, setTriageKey] = useState(0);
  const [accountId, setAccountId] = useState<string | undefined>();
  const [accountKey, setAccountKey] = useState(0);

  const analyzeTicket = (ticket: SupportTicket) => {
    setTriageTicket({ subject: ticket.subject, body: ticket.body, account_id: ticket.account_id });
    setTriageKey((key) => key + 1);
    setActiveTab("triage");
  };

  const inspectAccount = (account: SupportAccount) => {
    setAccountId(account.account_id);
    setAccountKey((key) => key + 1);
    setActiveTab("tam");
  };

  return (
    <main className="flex min-h-screen flex-col bg-[#0b111d] font-sans text-slate-100 selection:bg-sky-500/30">
      <Navbar activeTab={activeTab} onSelectTab={setActiveTab} />
      <div className="flex-1">
        {activeTab === "overview" && <OperationsDashboard onTriage={analyzeTicket} onAccount={inspectAccount} />}
        {activeTab === "triage" && <TriageStudio key={triageKey} initialTicket={triageTicket} />}
        {activeTab === "tam" && <TamMatrix key={accountKey} initialAccountId={accountId} />}
        {activeTab === "evals" && <EvalBenchmarks />}
      </div>
    </main>
  );
}