"use client";

import { useState } from "react";
import ThesisNotebook from "@/components/ThesisNotebook";
import TagApproval from "@/components/TagApproval";

type Tab = "thesis" | "approval";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("thesis");

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header with Tabs */}
      <div className="border-b border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between px-6 py-3">
          <h1 className="text-2xl font-semibold text-gray-600 tracking-tight italic">
            imprint
          </h1>
          <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab("thesis")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === "thesis"
                  ? "bg-white text-blue-600 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Thesis
            </button>
            <button
              onClick={() => setActiveTab("approval")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === "approval"
                  ? "bg-white text-blue-600 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Tag Approval
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "thesis" ? <ThesisNotebook /> : <TagApproval />}
      </div>
    </div>
  );
}
