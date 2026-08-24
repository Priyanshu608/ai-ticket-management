"use client";

import React, { useEffect, useState } from "react";
import { 
  Terminal, 
  ShieldCheck, 
  Layers, 
  Activity, 
  Cpu, 
  CheckCircle2, 
  AlertTriangle 
} from "lucide-react";
import { checkBackendHealth } from "@/lib/api";

interface NavbarProps {
  activeTab: "triage" | "tam" | "evals";
  onSelectTab: (tab: "triage" | "tam" | "evals") => void;
}

export default function Navbar({ activeTab, onSelectTab }: NavbarProps) {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    const verifyHealth = async () => {
      const isHealthy = await checkBackendHealth();
      if (mounted) setBackendOnline(isHealthy);
    };

    verifyHealth();
    const interval = setInterval(verifyHealth, 10000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="sticky top-0 z-50 border-b border-[#222634] bg-[#090a0f]/90 backdrop-blur-md px-4 py-2.5 flex items-center justify-between">
      {/* Brand & Pipeline Engine Info */}
      <div className="flex items-center space-x-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-600/10 border border-blue-500/30 text-blue-400">
          <Terminal className="h-4 w-4" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-mono text-sm font-semibold tracking-tight text-zinc-100">
              SUPPORT.AI
            </span>
            <span className="rounded border border-zinc-800 bg-zinc-900 px-1.5 py-0.5 text-[10px] font-mono font-medium text-zinc-400">
              v0.2.0
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 font-mono leading-none">
            FAISS · MiniLM · Groq Llama 3.3
          </p>
        </div>
      </div>

      {/* Navigation Switcher Tabs */}
      <nav className="flex items-center space-x-1 rounded-lg border border-[#222634] bg-[#11131a] p-1">
        <button
          onClick={() => onSelectTab("triage")}
          className={`flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
            activeTab === "triage"
              ? "bg-blue-600/20 text-blue-400 border border-blue-500/40 shadow-sm"
              : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent"
          }`}
        >
          <Cpu className="h-3.5 w-3.5" />
          <span>Triage Studio</span>
        </button>

        <button
          onClick={() => onSelectTab("tam")}
          className={`flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
            activeTab === "tam"
              ? "bg-blue-600/20 text-blue-400 border border-blue-500/40 shadow-sm"
              : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent"
          }`}
        >
          <Layers className="h-3.5 w-3.5" />
          <span>TAM Account Matrix</span>
        </button>

        <button
          onClick={() => onSelectTab("evals")}
          className={`flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
            activeTab === "evals"
              ? "bg-blue-600/20 text-blue-400 border border-blue-500/40 shadow-sm"
              : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 border border-transparent"
          }`}
        >
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Eval & Benchmarks</span>
        </button>
      </nav>

      {/* Live Backend Telemetry Indicator */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-1.5 rounded-full border border-zinc-800 bg-[#11131a] px-2.5 py-1 text-[11px] font-mono">
          <Activity className="h-3 w-3 text-zinc-500" />
          <span className="text-zinc-400">FastAPI API:</span>
          {backendOnline === null ? (
            <span className="text-zinc-500 animate-pulse">connecting...</span>
          ) : backendOnline ? (
            <span className="flex items-center text-emerald-400 font-semibold">
              <CheckCircle2 className="h-3 w-3 mr-1 text-emerald-400" /> 8000 ONLINE
            </span>
          ) : (
            <span className="flex items-center text-amber-400 font-semibold">
              <AlertTriangle className="h-3 w-3 mr-1 text-amber-400" /> OFFLINE
            </span>
          )}
        </div>
      </div>
    </header>
  );
}