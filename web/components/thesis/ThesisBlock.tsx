"use client";

import { useState } from "react";
import { Thesis, DragState, DragPayload } from "@/lib/types";
import Section from "./Section";

interface Props {
  thesis: Thesis;
  isActive: boolean;
  onActivate: () => void;
  onUpdate: (thesisId: string, update: any) => void;
  onAddSection: (thesisId: string) => void;
  onDeleteSection: (thesisId: string, sectionId: string) => void;
  onUpdateSection: (thesisId: string, sectionId: string, update: any) => void;
  dragState: DragState | null;
  startDrag: (payload: DragPayload, x: number, y: number) => void;
  registerZone: (
    id: string,
    el: HTMLElement | null,
    sectionId: string,
    thesisId: string
  ) => void;
}

export default function ThesisBlock({
  thesis,
  isActive,
  onActivate,
  onUpdate,
  onAddSection,
  onDeleteSection,
  onUpdateSection,
  dragState,
  startDrag,
  registerZone,
}: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const [editTitle, setEditTitle] = useState(false);
  const [draftTitle, setDraftTitle] = useState(thesis.title);

  return (
    <div
      className={`mb-8 rounded-xl transition-all cursor-pointer ${
        isActive
          ? "ring-2 ring-blue-200 bg-blue-50/20 p-4 -mx-4"
          : "p-4 -mx-4 hover:bg-gray-50/60"
      }`}
      onClick={onActivate}
    >
      <div className="flex items-center gap-2 mb-3">
        <button
          onClick={(e) => {
            e.stopPropagation();
            setCollapsed(!collapsed);
          }}
          className="text-gray-300 hover:text-gray-500 text-sm w-5 flex-shrink-0"
        >
          {collapsed ? "▸" : "▾"}
        </button>
        {editTitle ? (
          <input
            value={draftTitle}
            onChange={(e) => setDraftTitle(e.target.value)}
            onBlur={() => {
              onUpdate(thesis.id, { title: draftTitle });
              setEditTitle(false);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                onUpdate(thesis.id, { title: draftTitle });
                setEditTitle(false);
              }
            }}
            onClick={(e) => e.stopPropagation()}
            autoFocus
            className="text-lg font-bold text-gray-900 flex-1 focus:outline-none border-b-2 border-blue-500 bg-transparent"
          />
        ) : (
          <h2
            className="text-lg font-bold text-gray-900 flex-1 hover:text-blue-600 transition-colors"
            onDoubleClick={(e) => {
              e.stopPropagation();
              setEditTitle(true);
            }}
          >
            {thesis.title}
          </h2>
        )}
        {isActive && (
          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
            active
          </span>
        )}
      </div>

      {!collapsed && (
        <div className="ml-5" onClick={(e) => e.stopPropagation()}>
          {thesis.sections.map((s) => (
            <Section
              key={s.id}
              section={s}
              thesisId={thesis.id}
              onUpdate={onUpdateSection}
              onDelete={onDeleteSection}
              dragState={dragState}
              startDrag={startDrag}
              registerZone={registerZone}
            />
          ))}
          <button
            onClick={() => onAddSection(thesis.id)}
            className="flex items-center gap-1.5 px-2 py-1.5 text-xs text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors mt-1"
          >
            <span className="text-base leading-none">+</span> Add section
          </button>
        </div>
      )}
      <div className="mt-5 border-b border-gray-100 -mx-4" />
    </div>
  );
}
