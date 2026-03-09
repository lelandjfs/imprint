"use client";

import { useState } from "react";
import ChatInterface from "@/components/ChatInterface";
import TagApproval from "@/components/TagApproval";

type Tab = "chat" | "approval";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("chat");

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header with Tabs */}
      <div className="border-b border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between px-6 py-3">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Imprint
          </h1>
          <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab("chat")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === "chat"
                  ? "bg-white text-blue-600 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Chat
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
        {activeTab === "chat" ? <ChatInterface /> : <TagApproval />}
      </div>
    </div>
  );
}
