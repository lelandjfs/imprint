"use client";

import { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { Message, ChatFilters, FilterOptions, Document, ModelInfo } from "@/lib/types";
import { streamChat, getFilters, getModels } from "@/lib/api";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import FilterSidebar from "./FilterSidebar";
import SourcesPanel from "./SourcesPanel";

export default function ChatInterface() {
  const [sessionId] = useState(() => uuidv4());
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filters, setFilters] = useState<ChatFilters>({});
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [currentSources, setCurrentSources] = useState<Document[]>([]);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("claude-3-5-sonnet-20241022");

  // Load filter options and models on mount
  useEffect(() => {
    getFilters().then(setFilterOptions).catch(console.error);
    getModels().then((data) => {
      setModels(data.models);
      setSelectedModel(data.default);
    }).catch(console.error);
  }, []);

  const handleSend = async (message: string) => {
    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      role: "user",
      content: message,
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Create placeholder for assistant message
    const assistantId = uuidv4();
    const assistantMessage: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
    };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      let fullResponse = "";
      let sources: Document[] = [];

      for await (const event of streamChat(sessionId, message, selectedModel, filters)) {
        if (event.type === "sources") {
          sources = event.documents || [];
          setCurrentSources(sources);
          setSourcesOpen(true);
        } else if (event.type === "token") {
          fullResponse += event.content || "";
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: fullResponse, sources }
                : m
            )
          );
        } else if (event.type === "done") {
          fullResponse = event.full_response || fullResponse;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: fullResponse, sources }
                : m
            )
          );
        } else if (event.type === "error") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: `Error: ${event.message}` }
                : m
            )
          );
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: "Sorry, an error occurred. Please try again." }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Filter Sidebar */}
      <FilterSidebar
        filters={filters}
        filterOptions={filterOptions}
        onFiltersChange={setFilters}
        onClear={() => setFilters({})}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 p-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">Imprint Chat</h1>
          <div className="flex items-center gap-4">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="rounded border border-gray-300 px-3 py-1 text-sm"
            >
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
            <button
              onClick={() => setSourcesOpen(!sourcesOpen)}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {sourcesOpen ? "Hide" : "Show"} Sources
            </button>
          </div>
        </div>

        {/* Messages */}
        <MessageList messages={messages} />

        {/* Input */}
        <MessageInput onSend={handleSend} disabled={isLoading} />
      </div>

      {/* Sources Panel */}
      <SourcesPanel
        sources={currentSources}
        isOpen={sourcesOpen}
        onClose={() => setSourcesOpen(false)}
      />
    </div>
  );
}
