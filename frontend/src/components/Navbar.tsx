"use client";

import { useEffect, useState } from "react";
import { Activity, BrainCircuit, ChartNoAxesColumnIncreasing, CircleCheck, CircleAlert, Command, LayoutDashboard, Users } from "lucide-react";
import { checkBackendHealth } from "@/lib/api";

export type WorkspaceTab = "overview" | "triage" | "tam" | "evals";

const tabs = [
  { id: "overview", name: "Overview", icon: LayoutDashboard },
  { id: "triage", name: "AI Triage", icon: BrainCircuit },
  { id: "tam", name: "Account Health", icon: Users },
  { id: "evals", name: "Evaluation", icon: ChartNoAxesColumnIncreasing },
] as const;

export default function Navbar({ activeTab, onSelectTab }: {
  activeTab: WorkspaceTab;
  onSelectTab: (tab: WorkspaceTab) => void;
}) {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    const verify = () => {
      checkBackendHealth().then((value) => { if (mounted) setOnline(value); });
    };
    verify();
    const interval = setInterval(verify, 15000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.07] bg-[#0b111d]/95 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1580px] flex-wrap items-center justify-between gap-x-5 gap-y-3 px-4 py-3 sm:px-7 lg:px-10">
        <div className="flex min-w-[165px] items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-sky-300/20 bg-sky-400/10 text-sky-300">
            <Command className="h-5 w-5" />
          </div>
          <div>
            <div className="text-base font-bold tracking-tight text-white">Support<span className="text-sky-400">Flow</span></div>
            <p className="mt-0.5 text-[10px] uppercase tracking-[0.19em] text-slate-500">Intelligence workspace</p>
          </div>
        </div>

        <nav aria-label="Workspace navigation" className="order-3 flex w-full items-center gap-1 overflow-x-auto rounded-xl border border-white/[0.07] bg-white/[0.025] p-1 sm:order-2 sm:w-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button key={tab.id} type="button" onClick={() => onSelectTab(tab.id)}
                aria-current={activeTab === tab.id ? "page" : undefined}
                className={`inline-flex shrink-0 items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-sky-400 ${activeTab === tab.id
                  ? "bg-sky-500/15 text-sky-200 shadow-sm ring-1 ring-sky-500/20"
                  : "text-slate-400 hover:bg-white/[0.06] hover:text-slate-100"}`}>
                <Icon className="h-4 w-4" />{tab.name}
              </button>
            );
          })}
        </nav>

        <div role="status" aria-live="polite" className="order-2 flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.025] px-3 py-2 text-[11px] font-medium text-slate-300 sm:order-3">
          {online === null ? <Activity className="h-3.5 w-3.5 animate-pulse text-slate-500" />
            : online ? <CircleCheck className="h-3.5 w-3.5 text-emerald-400" />
              : <CircleAlert className="h-3.5 w-3.5 text-amber-400" />}
          <span>{online === null ? "Connecting" : online ? "API connected" : "API offline"}</span>
        </div>
      </div>
    </header>
  );
}
