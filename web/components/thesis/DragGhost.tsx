"use client";

import { DragState } from "@/lib/types";

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
  dragState: DragState | null;
}

export default function DragGhost({ dragState }: Props) {
  if (!dragState) return null;

  return (
    <div
      className="fixed pointer-events-none z-50 bg-white border-2 border-blue-500 rounded-full px-3 py-1.5 shadow-2xl text-xs font-semibold flex items-center gap-2 max-w-xs"
      style={{
        left: dragState.x + 14,
        top: dragState.y - 14,
        transform: "rotate(-1deg)",
      }}
    >
      <div
        className={`w-2 h-2 rounded-full flex-shrink-0 ${sentimentDot(
          dragState.payload.citation.sentiment
        )}`}
      />
      <span className="truncate">{dragState.payload.citation.title}</span>
    </div>
  );
}
