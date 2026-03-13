"use client";

import { useState } from "react";
import { Document, DragState, DragPayload } from "@/lib/types";

const sentimentDot = (s: string | null) => {
  const map: Record<string, string> = {
    bullish: "bg-emerald-400",
    bearish: "bg-red-400",
    neutral: "bg-gray-300",
    mixed: "bg-amber-400",
  };
  return map[s || ""] || "bg-gray-300";
};

const sectorColor = (s: string | null) => {
  const map: Record<string, string> = {
    Energy: "text-amber-700 bg-amber-50 border-amber-200",
    Semiconductors: "text-blue-700 bg-blue-50 border-blue-200",
    Infra: "text-purple-700 bg-purple-50 border-purple-200",
    Software: "text-indigo-700 bg-indigo-50 border-indigo-200",
  };
  return map[s || ""] || "text-gray-600 bg-gray-100 border-gray-200";
};

interface Props {
  source: Document;
  onAdd: (source: Document) => void;
  alreadyCited: boolean;
  activeThesisTitle: string | null;
  startDrag: (payload: DragPayload, x: number, y: number) => void;
  dragState: DragState | null;
}

export default function SidebarSourceCard({
  source,
  onAdd,
  alreadyCited,
  activeThesisTitle,
  startDrag,
  dragState,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const isBeingDragged =
    dragState?.payload?.citation?.document_id === source.id.toString() &&
    dragState?.payload?.origin === "sidebar";

  const onPointerDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return;
    if ((e.target as HTMLElement).closest("button")) return;
    e.preventDefault();

    const citation = {
      id: source.id.toString(), // Will be replaced with real citation ID on server
      title: source.title,
      sector: source.sector,
      sentiment: source.sentiment,
      summary: source.summary,
      document_id: source.id.toString(),
      position: 0,
    };

    startDrag(
      {
        citation,
        origin: "sidebar",
        fromSectionId: null,
        fromThesisId: null,
      },
      e.clientX,
      e.clientY
    );
  };

  return (
    <div
      onPointerDown={onPointerDown}
      className={`rounded-lg border bg-white select-none transition-all ${
        isBeingDragged
          ? "opacity-40"
          : "cursor-grab hover:border-blue-300 hover:shadow-sm"
      } ${alreadyCited ? "border-blue-200 bg-blue-50/30" : "border-gray-200"}`}
    >
      <div className="flex items-start gap-2 p-2.5">
        <div className="flex flex-col gap-[3px] mt-2 flex-shrink-0 opacity-20">
          {[0, 1, 2].map((i) => (
            <div key={i} className="w-2.5 h-[2px] bg-gray-500 rounded-full" />
          ))}
        </div>
        <div
          className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${sentimentDot(
            source.sentiment
          )}`}
        />
        <div className="flex-1 min-w-0">
          <div
            className="text-xs font-medium text-gray-800 leading-snug cursor-pointer hover:text-blue-600"
            onClick={() => setExpanded(!expanded)}
          >
            {source.title}
          </div>
          <div className="flex items-center gap-1.5 mt-1">
            {source.sector && (
              <span
                className={`text-xs px-1.5 py-0.5 rounded border font-medium ${sectorColor(
                  source.sector
                )}`}
              >
                {source.sector}
              </span>
            )}
          </div>
          {expanded && source.summary && (
            <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">
              {source.summary}
            </p>
          )}
        </div>
        {alreadyCited ? (
          <span className="text-xs text-blue-400 mt-0.5 font-medium">✓</span>
        ) : (
          <button
            onClick={() => onAdd(source)}
            title={
              activeThesisTitle
                ? `Add to ${activeThesisTitle}`
                : "Add to thesis"
            }
            className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-md bg-gray-100 hover:bg-blue-600 hover:text-white text-gray-500 transition-colors text-sm font-bold mt-0.5"
          >
            +
          </button>
        )}
      </div>
    </div>
  );
}
