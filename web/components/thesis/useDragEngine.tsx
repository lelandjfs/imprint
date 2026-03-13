"use client";

import { useState, useRef, useCallback } from "react";
import { DragState, DragPayload } from "@/lib/types";

/**
 * Custom drag engine using pointer events (no HTML5 DnD)
 *
 * Features:
 * - Window-level pointermove/pointerup listeners
 * - Hit testing against registered drop zones
 * - No setPointerCapture (mobile-friendly)
 */
export function useDragEngine(
  onDrop: (payload: DragPayload, toSectionId: string, toThesisId: string) => void
) {
  const [dragState, setDragState] = useState<DragState | null>(null);

  // { id: { el, sectionId, thesisId } }
  const zonesRef = useRef<Record<string, {
    el: HTMLElement;
    sectionId: string;
    thesisId: string;
  }>>({});

  // Mirror of dragState for use inside callbacks
  const stateRef = useRef<DragState | null>(null);

  const registerZone = useCallback((
    id: string,
    el: HTMLElement | null,
    sectionId: string,
    thesisId: string
  ) => {
    if (el) {
      zonesRef.current[id] = { el, sectionId, thesisId };
    } else {
      delete zonesRef.current[id];
    }
  }, []);

  const startDrag = useCallback((
    payload: DragPayload,
    clientX: number,
    clientY: number
  ) => {
    const state: DragState = {
      payload,
      x: clientX,
      y: clientY,
      overZoneId: null,
    };
    stateRef.current = state;
    setDragState({ ...state });

    // Hit test helper
    function hitTest(mx: number, my: number): string | null {
      for (const [id, zone] of Object.entries(zonesRef.current)) {
        const r = zone.el.getBoundingClientRect();
        if (mx >= r.left && mx <= r.right && my >= r.top && my <= r.bottom) {
          return id;
        }
      }
      return null;
    }

    function onMove(e: PointerEvent) {
      const overZoneId = hitTest(e.clientX, e.clientY);
      const next: DragState = {
        ...stateRef.current!,
        x: e.clientX,
        y: e.clientY,
        overZoneId,
      };
      stateRef.current = next;
      setDragState({ ...next });
    }

    function onUp(e: PointerEvent) {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);

      const zoneId = hitTest(e.clientX, e.clientY);
      if (zoneId) {
        const zone = zonesRef.current[zoneId];
        onDrop(stateRef.current!.payload, zone.sectionId, zone.thesisId);
      }

      stateRef.current = null;
      setDragState(null);
    }

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }, [onDrop]);

  return { dragState, startDrag, registerZone };
}
