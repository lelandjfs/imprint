"use client";

import { ThesisCitation, DragPayload } from "@/lib/types";

const sentimentDot = (s: string | null) => {
  const map: Record<string, string> = {
    bullish: "bg-emerald-400",
    bearish: "bg-red-400",
    neutral: "bg-gray-300",
    mixed: "bg-amber-400",
  };
  return map[s || ""] || "bg-gray-300";
};

interface Props {
  citation: ThesisCitation;
  sectionId: string;
  thesisId: string;
  onRemove: (citationId: string) => void;
  startDrag: (payload: DragPayload, x: number, y: number) => void;
  isBeingDragged: boolean;
}

export default function CitationChip({
  citation,
  sectionId,
  thesisId,
  onRemove,
  startDrag,
  isBeingDragged,
}: Props) {
  const onPointerDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return;
    if ((e.target as HTMLElement).closest("button")) return;
    e.preventDefault(); // prevent text selection

    startDrag(
      {
        citation,
        origin: "chip",
        fromSectionId: sectionId,
        fromThesisId: thesisId,
      },
      e.clientX,
      e.clientY
    );
  };

  return (
    <div
      onPointerDown={onPointerDown}
      className={`group inline-flex items-center gap-1.5 px-2.5 py-1 bg-white border border-gray-200 rounded-full text-xs text-gray-600 cursor-grab hover:border-blue-300 hover:shadow-sm transition-all select-none ${
        isBeingDragged ? "opacity-30" : ""
      }`}
    >
      <div
        className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${sentimentDot(
          citation.sentiment
        )}`}
      />
      <span className="truncate max-w-[180px]">{citation.title}</span>
      <button
        className="text-gray-300 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity ml-0.5"
        onClick={(e) => {
          e.stopPropagation();
          onRemove(citation.id);
        }}
      >
        ×
      </button>
    </div>
  );
}
