"use client";

import { useState, useRef, useEffect } from "react";
import { ThesisSection, DragState, DragPayload } from "@/lib/types";
import CitationChip from "./CitationChip";
import DropZone from "./DropZone";

interface Props {
  section: ThesisSection;
  thesisId: string;
  onUpdate: (thesisId: string, sectionId: string, update: any) => void;
  onDelete: (thesisId: string, sectionId: string) => void;
  dragState: DragState | null;
  startDrag: (payload: DragPayload, x: number, y: number) => void;
  registerZone: (
    id: string,
    el: HTMLElement | null,
    sectionId: string,
    thesisId: string
  ) => void;
}

export default function Section({
  section,
  thesisId,
  onUpdate,
  onDelete,
  dragState,
  startDrag,
  registerZone,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(section.content);
  const [editTitle, setEditTitle] = useState(false);
  const [draftTitle, setDraftTitle] = useState(section.title);
  const ta = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editing) ta.current?.focus();
  }, [editing]);

  const dzId = `dz-${section.id}`;
  const isDragging = !!dragState;
  const isOver = dragState?.overZoneId === dzId;
  const isSelf = dragState?.payload?.fromSectionId === section.id;
  const chipBeingDragged = dragState?.payload?.citation?.id;
  const chipFromHere = dragState?.payload?.fromSectionId === section.id;

  return (
    <div className="mb-2 rounded-lg group/section">
      {/* Title row */}
      <div className="flex items-center gap-1.5 py-1 px-1">
        <button
          onClick={() =>
            onUpdate(thesisId, section.id, { collapsed: !section.collapsed })
          }
          className="text-gray-300 hover:text-gray-500 text-xs w-4 flex-shrink-0"
        >
          {section.collapsed ? "▸" : "▾"}
        </button>
        {editTitle ? (
          <input
            value={draftTitle}
            onChange={(e) => setDraftTitle(e.target.value)}
            onBlur={() => {
              onUpdate(thesisId, section.id, { title: draftTitle });
              setEditTitle(false);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                onUpdate(thesisId, section.id, { title: draftTitle });
                setEditTitle(false);
              }
            }}
            autoFocus
            className="text-sm font-semibold text-gray-700 flex-1 focus:outline-none border-b border-blue-400 bg-transparent"
          />
        ) : (
          <span
            className="text-sm font-semibold text-gray-700 flex-1 cursor-pointer hover:text-gray-900"
            onDoubleClick={() => setEditTitle(true)}
          >
            {section.title}
          </span>
        )}
        <button
          onClick={() => onDelete(thesisId, section.id)}
          className="text-gray-200 hover:text-red-400 text-xs opacity-0 group-hover/section:opacity-100 px-1"
        >
          ✕
        </button>
      </div>

      {!section.collapsed && (
        <div className="ml-6 mb-2 pr-2">
          {/* Content editing */}
          {editing ? (
            <div>
              <textarea
                ref={ta}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                rows={4}
                className="w-full text-sm text-gray-700 leading-relaxed border border-blue-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-100 resize-none bg-blue-50/20"
              />
              <div className="flex gap-2 mt-1.5">
                <button
                  onClick={() => {
                    onUpdate(thesisId, section.id, { content: draft });
                    setEditing(false);
                  }}
                  className="px-3 py-1 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setDraft(section.content);
                    setEditing(false);
                  }}
                  className="px-3 py-1 text-xs text-gray-400 hover:text-gray-700"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div
              onClick={() => {
                setDraft(section.content);
                setEditing(true);
              }}
              className={`text-sm leading-relaxed cursor-text rounded-lg p-2 -ml-2 hover:bg-gray-50 transition-colors min-h-[1.5rem] ${
                section.content
                  ? "text-gray-600 whitespace-pre-line"
                  : "text-gray-300 italic"
              }`}
            >
              {section.content || "Write something..."}
            </div>
          )}

          {/* Citations */}
          {section.citations.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {section.citations.map((c) => (
                <CitationChip
                  key={c.id}
                  citation={c}
                  sectionId={section.id}
                  thesisId={thesisId}
                  onRemove={(id) =>
                    onUpdate(thesisId, section.id, {
                      citations: section.citations.filter((x) => x.id !== id),
                    })
                  }
                  startDrag={startDrag}
                  isBeingDragged={chipFromHere && chipBeingDragged === c.id}
                />
              ))}
            </div>
          )}

          {/* Drop zone */}
          <DropZone
            id={dzId}
            sectionId={section.id}
            thesisId={thesisId}
            isOver={isOver}
            isSelf={isSelf}
            registerZone={registerZone}
            isDragging={isDragging}
          />
        </div>
      )}
    </div>
  );
}
