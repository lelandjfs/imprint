"use client";

import { useState, useRef, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { Thesis, Document, DragState, DragPayload, QueryAnalysis } from "@/lib/types";
import { streamChat, submitFeedback } from "@/lib/api";
import SidebarSourceCard from "./SidebarSourceCard";

interface Message {
  role: "user" | "assistant";
  text: string;
  sources?: Document[];
  queryAnalysis?: QueryAnalysis;
  runId?: string;
  feedback?: number; // 1 for thumbs up, 0 for thumbs down, undefined if not given
}

interface Props {
  theses: Thesis[];
  activeThesisId: string | null;
  onAddSource: (source: Document) => void;
  onAddText: (text: string) => void;
  dragState: DragState | null;
  startDrag: (payload: DragPayload, x: number, y: number) => void;
}

export default function ChatSidebar({
  theses,
  activeThesisId,
  onAddSource,
  onAddText,
  dragState,
  startDrag,
}: Props) {
  const [sessionId] = useState(() => uuidv4());
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("claude-sonnet-4-5-20250929");
  const bottomRef = useRef<HTMLDivElement>(null);

  const activeThesis = theses.find((t) => t.id === activeThesisId);
  const activeCitedIds = activeThesis
    ? activeThesis.sections.flatMap((s) => s.citations.map((c) => c.document_id))
    : [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleFeedback = async (messageIndex: number, score: number) => {
    const message = messages[messageIndex];
    if (!message.runId) return;

    try {
      await submitFeedback(message.runId, score);
      // Update message with feedback
      setMessages((prev) =>
        prev.map((msg, idx) =>
          idx === messageIndex ? { ...msg, feedback: score } : msg
        )
      );
    } catch (error) {
      console.error("Failed to submit feedback:", error);
    }
  };

  const send = async () => {
    if (!input.trim()) return;

    const q = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setLoading(true);

    try {
      let fullResponse = "";
      let sources: Document[] = [];
      let queryAnalysis: QueryAnalysis | undefined;
      let runId: string | undefined;

      // Use real SSE streaming
      for await (const event of streamChat(sessionId, q, selectedModel)) {
        if (event.type === "query_analysis") {
          queryAnalysis = event.analysis;
        } else if (event.type === "sources") {
          sources = event.documents || [];
        } else if (event.type === "token") {
          fullResponse += event.content || "";
        } else if (event.type === "done") {
          fullResponse = event.full_response || fullResponse;
        } else if (event.type === "run_id") {
          runId = event.run_id;
        } else if (event.type === "error") {
          console.error("Chat error:", event.message);
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: fullResponse,
          sources,
          queryAnalysis,
          runId,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Sorry, there was an error processing your request.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-72 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col h-full">
      <div className="px-4 py-3 border-b border-gray-200 flex-shrink-0">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Chat
        </div>
        {activeThesis ? (
          <div className="text-xs text-gray-400 mt-0.5">
            Active:{" "}
            <span className="text-blue-600 font-medium">
              {activeThesis.title}
            </span>
          </div>
        ) : (
          <div className="text-xs text-gray-400 mt-0.5">
            Click a thesis to activate
          </div>
        )}
        <div className="flex items-center gap-2 mt-2">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="flex-1 px-2 py-1 text-xs border border-gray-200 rounded bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="claude-sonnet-4-5-20250929">Claude Sonnet 4.5</option>
            <option value="claude-opus-4-5">Claude Opus 4.5</option>
            <option value="gpt-4o">GPT-4o</option>
            <option value="gpt-4o-mini">GPT-4o Mini</option>
          </select>
          <button
            onClick={() => setMessages([])}
            className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 rounded border border-gray-200 transition-colors whitespace-nowrap"
            title="Clear conversation"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
        {messages.length === 0 && (
          <div className="pt-8 px-2 text-center">
            <div className="text-xl mb-2">💬</div>
            <div className="text-xs text-gray-400 leading-relaxed">
              Ask questions about your research.
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === "user" ? (
              <div className="flex justify-end">
                <div className="bg-blue-600 text-white text-xs px-3 py-2 rounded-2xl rounded-tr-sm max-w-[90%] leading-relaxed">
                  {msg.text}
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="bg-gray-50 border border-gray-200 text-gray-700 text-xs px-3 py-2.5 rounded-2xl rounded-tl-sm leading-relaxed">
                  {msg.text}
                  <div className="mt-2 pt-2 border-t border-gray-200 flex items-center justify-between">
                    {activeThesis && (
                      <button
                        onClick={() => onAddText(msg.text)}
                        className="flex items-center gap-1.5 text-gray-400 hover:text-blue-600 transition-colors"
                      >
                        <span className="text-sm">+</span>
                        <span className="text-xs">add to {activeThesis.title}</span>
                      </button>
                    )}
                    {msg.runId && (
                      <div className="flex items-center gap-0.5">
                        <button
                          onClick={() => handleFeedback(i, 1)}
                          className={`p-1 rounded transition-all ${
                            msg.feedback === 1
                              ? "text-green-600"
                              : "text-gray-300 hover:text-gray-500"
                          }`}
                          title="Good response"
                        >
                          <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleFeedback(i, 0)}
                          className={`p-1 rounded transition-all ${
                            msg.feedback === 0
                              ? "text-red-600"
                              : "text-gray-300 hover:text-gray-500"
                          }`}
                          title="Bad response"
                        >
                          <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
                {msg.queryAnalysis && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 text-xs">
                    <div className="font-semibold text-blue-700 mb-1">Query Analysis:</div>
                    <div className="space-y-0.5 text-gray-600">
                      {msg.queryAnalysis.topic && (
                        <div><span className="font-medium">Topic:</span> {msg.queryAnalysis.topic}</div>
                      )}
                      {msg.queryAnalysis.entities.length > 0 && (
                        <div><span className="font-medium">Entities:</span> {msg.queryAnalysis.entities.join(", ")}</div>
                      )}
                      {msg.queryAnalysis.sectors.length > 0 && (
                        <div><span className="font-medium">Sectors:</span> {msg.queryAnalysis.sectors.join(", ")}</div>
                      )}
                      {msg.queryAnalysis.sentiment_intent && (
                        <div><span className="font-medium">Sentiment:</span> {msg.queryAnalysis.sentiment_intent}</div>
                      )}
                      {msg.queryAnalysis.catalyst_window && (
                        <div><span className="font-medium">Time Horizon:</span> {msg.queryAnalysis.catalyst_window}</div>
                      )}
                      <div><span className="font-medium">Intent:</span> {msg.queryAnalysis.search_intent}</div>
                    </div>
                  </div>
                )}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="space-y-1.5 pl-0.5">
                    {msg.sources.map((src) => (
                      <SidebarSourceCard
                        key={src.id}
                        source={src}
                        onAdd={onAddSource}
                        activeThesisTitle={activeThesis?.title || null}
                        alreadyCited={activeCitedIds.includes(src.id.toString())}
                        startDrag={startDrag}
                        dragState={dragState}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-1 px-1 py-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex-shrink-0 p-3 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask your research..."
            className="flex-1 px-3 py-2 text-xs border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50"
          />
          <button
            onClick={send}
            disabled={!input.trim() || loading}
            className="px-3 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-40 transition-colors text-sm flex-shrink-0"
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}
