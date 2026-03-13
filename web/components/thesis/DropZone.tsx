"use client";

import { useRef, useEffect } from "react";

interface Props {
  id: string;
  sectionId: string;
  thesisId: string;
  isOver: boolean;
  isSelf: boolean;
  registerZone: (
    id: string,
    el: HTMLElement | null,
    sectionId: string,
    thesisId: string
  ) => void;
  isDragging: boolean;
}

export default function DropZone({
  id,
  sectionId,
  thesisId,
  isOver,
  isSelf,
  registerZone,
  isDragging,
}: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    registerZone(id, ref.current, sectionId, thesisId);
    return () => registerZone(id, null, sectionId, thesisId);
  }, [id, sectionId, thesisId, registerZone]);

  return (
    <div
      ref={ref}
      className={`mt-2 rounded-lg border-2 border-dashed py-2 text-center text-xs font-medium transition-all duration-100 ${
        !isDragging
          ? "border-transparent text-transparent h-0 mt-0 py-0 overflow-hidden"
          : isSelf
          ? "border-gray-200 text-gray-300"
          : isOver
          ? "border-blue-400 bg-blue-50 text-blue-500"
          : "border-gray-200 text-gray-300"
      }`}
    >
      {isDragging && (isSelf ? "current" : isOver ? "↓ drop here" : "drop zone")}
    </div>
  );
}
