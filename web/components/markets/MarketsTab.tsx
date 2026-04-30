/**
 * MarketsTab - Main Markets tab with Explore and Thesis Alignment sub-tabs
 */

"use client";

import { useState } from "react";
import ExploreView from "./ExploreView";
import ThesisAlignmentView from "./ThesisAlignmentView";
import ThesisSelector from "./ThesisSelector";

type SubTab = "explore" | "alignment";

interface Thesis {
  id: string;
  title: string;
}

interface MarketsTabProps {
  theses: Thesis[];
}

export default function MarketsTab({ theses }: MarketsTabProps) {
  const [subTab, setSubTab] = useState<SubTab>("explore");
  const [selectedThesisId, setSelectedThesisId] = useState<string | null>(null);

  return (
    <div className="h-full flex flex-col bg-gray-950 text-gray-100">
      {/* Sub-tab navigation */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-800">
        <div className="flex gap-1 bg-gray-900 p-1 rounded">
          <button
            onClick={() => setSubTab("explore")}
            className={`px-4 py-1.5 text-sm font-mono transition-colors rounded ${
              subTab === "explore"
                ? "bg-gray-800 text-emerald-400"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            Explore
          </button>
          <button
            onClick={() => setSubTab("alignment")}
            className={`px-4 py-1.5 text-sm font-mono transition-colors rounded ${
              subTab === "alignment"
                ? "bg-gray-800 text-emerald-400"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            Thesis Alignment
          </button>
        </div>

        {subTab === "alignment" && (
          <ThesisSelector
            theses={theses}
            selectedId={selectedThesisId}
            onSelect={setSelectedThesisId}
          />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {subTab === "explore" ? (
          <ExploreView />
        ) : (
          <ThesisAlignmentView thesisId={selectedThesisId} />
        )}
      </div>
    </div>
  );
}
