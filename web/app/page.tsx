"use client";

import { useState, useEffect } from "react";
import ThesisNotebook from "@/components/ThesisNotebook";
import TagApproval from "@/components/TagApproval";
import MarketsTab from "@/components/markets/MarketsTab";
import { getTheses } from "@/lib/api";

type Tab = "thesis" | "approval" | "markets";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("thesis");
  const [theses, setTheses] = useState<{ id: string; title: string }[]>([]);

  // Load theses for Markets tab
  useEffect(() => {
    const loadTheses = async () => {
      try {
        const data = await getTheses();
        setTheses(
          data.theses.map((t: any) => ({ id: t.id, title: t.title }))
        );
      } catch (error) {
        console.error("Failed to load theses:", error);
      }
    };
    loadTheses();
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      {/* Header with Tabs */}
      <div className="border-b border-gray-800 bg-gray-900">
        <div className="flex items-center justify-between px-6 py-3">
          <h1 className="text-2xl font-semibold text-gray-400 tracking-tight italic font-mono">
            imprint
          </h1>
          <div className="flex gap-1 bg-gray-950 p-1 rounded">
            <button
              onClick={() => setActiveTab("thesis")}
              className={`px-4 py-2 rounded text-sm font-medium font-mono transition-all ${
                activeTab === "thesis"
                  ? "bg-gray-800 text-emerald-400"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Thesis
            </button>
            <button
              onClick={() => setActiveTab("approval")}
              className={`px-4 py-2 rounded text-sm font-medium font-mono transition-all ${
                activeTab === "approval"
                  ? "bg-gray-800 text-emerald-400"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Tag Approval
            </button>
            <button
              onClick={() => setActiveTab("markets")}
              className={`px-4 py-2 rounded text-sm font-medium font-mono transition-all ${
                activeTab === "markets"
                  ? "bg-gray-800 text-emerald-400"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Markets
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "thesis" && <ThesisNotebook />}
        {activeTab === "approval" && <TagApproval />}
        {activeTab === "markets" && <MarketsTab theses={theses} />}
      </div>
    </div>
  );
}
