"use client";

import { useState, useRef, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { Thesis, Document, DragState, DragPayload } from "@/lib/types";
import { streamChat } from "@/lib/api";
import SidebarSourceCard from "./SidebarSourceCard";

interface Message {
  role: "user" | "assistant";
  text: string;
  sources?: Document[];
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
  const [selectedModel] = useState("claude-sonnet-4-5-20250929");
  const bottomRef = useRef<HTMLDivElement>(null);

  const activeThesis = theses.find((t) => t.id === activeThesisId);
  const activeCitedIds = activeThesis
    ? activeThesis.sections.flatMap((s) => s.citations.map((c) => c.document_id))
    : [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async () => {
    if (!input.trim()) return;

    const q = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setLoading(true);

    try {
      let fullResponse = "";
      let sources: Document[] = [];

      // Use real SSE streaming
      for await (const event of streamChat(sessionId, q, selectedModel)) {
        if (event.type === "sources") {
          sources = event.documents || [];
        } else if (event.type === "token") {
          fullResponse += event.content || "";
        } else if (event.type === "done") {
          fullResponse = event.full_response || fullResponse;
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
                  {activeThesis && (
                    <button
                      onClick={() => onAddText(msg.text)}
                      className="mt-2 pt-2 border-t border-gray-200 w-full flex items-center gap-1.5 text-gray-400 hover:text-blue-600 transition-colors"
                    >
                      <span className="text-sm">+</span>
                      <span className="text-xs">add to {activeThesis.title}</span>
                    </button>
                  )}
                </div>
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
