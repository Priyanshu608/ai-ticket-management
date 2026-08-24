"use client";

import React, { useState } from "react";
import Navbar from "@/components/Navbar";
import TriageStudio from "@/components/TriageStudio";
import TamMatrix from "@/components/TamMatrix";
import EvalBenchmarks from "@/components/EvalBenchmarks";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"triage" | "tam" | "evals">("triage");

  return (
    <main className="min-h-screen bg-[#090a0f] bg-tech-grid flex flex-col font-sans text-zinc-100 selection:bg-blue-600 selection:text-white">
      {/* Top Telemetry Header */}
      <Navbar activeTab={activeTab} onSelectTab={setActiveTab} />

      {/* Dynamic Viewport Container */}
      <div className="flex-1 pb-12">
        {activeTab === "triage" && <TriageStudio />}
        {activeTab === "tam" && <TamMatrix />}
        {activeTab === "evals" && <EvalBenchmarks />}
      </div>
    </main>
  );
}