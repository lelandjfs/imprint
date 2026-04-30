"use client";

import { useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import { Thesis, Document } from "@/lib/types";
import {
  getTheses,
  createThesis,
  updateThesis,
  createSection,
  updateSection,
  deleteSection,
  addCitation,
  removeCitation,
  moveCitation,
} from "@/lib/api";
import { useDragEngine } from "./thesis/useDragEngine";
import ThesisBlock from "./thesis/ThesisBlock";
import ChatSidebar from "./thesis/ChatSidebar";
import DragGhost from "./thesis/DragGhost";
import Toast from "./thesis/Toast";

export default function ThesisNotebook() {
  const [theses, setTheses] = useState<Thesis[]>([]);
  const [initialTheses, setInitialTheses] = useState<Thesis[]>([]); // For tracking changes
  const [activeThesisId, setActiveThesisId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState({ visible: false, message: "" });

  const hasUnsavedChanges = JSON.stringify(theses) !== JSON.stringify(initialTheses);

  // Load theses on mount
  useEffect(() => {
    loadTheses();
  }, []);

  const loadTheses = async () => {
    try {
      const data = await getTheses();
      setTheses(data.theses);
      setInitialTheses(JSON.parse(JSON.stringify(data.theses))); // Deep copy
      if (data.theses.length > 0 && !activeThesisId) {
        setActiveThesisId(data.theses[0].id);
      }
    } catch (error) {
      console.error("Failed to load theses:", error);
    } finally {
      setLoading(false);
    }
  };

  // Save all changes to database
  const saveAllChanges = async () => {
    if (!hasUnsavedChanges) return;

    setSaving(true);
    try {
      const initialMap = new Map(initialTheses.map((t) => [t.id, t]));
      const currentMap = new Map(theses.map((t) => [t.id, t]));

      // Process each current thesis
      for (const thesis of theses) {
        const initial = initialMap.get(thesis.id);

        if (!initial) {
          // New thesis - create it and all its sections/citations
          const createdThesis = await createThesis(thesis.title);

          for (const section of thesis.sections) {
            const createdSection = await createSection(createdThesis.id);

            // Update section if it has content or non-default title
            if (section.title !== "Untitled Section" || section.content) {
              await updateSection(createdThesis.id, createdSection.id, {
                title: section.title,
                content: section.content,
              });
            }

            // Add citations
            for (const citation of section.citations) {
              await addCitation(createdThesis.id, createdSection.id, citation.document_id);
            }
          }
        } else {
          // Existing thesis - check for updates
          if (thesis.title !== initial.title) {
            await updateThesis(thesis.id, { title: thesis.title });
          }

          // Process sections
          const initialSections = new Map(initial.sections.map((s) => [s.id, s]));
          const currentSections = new Map(thesis.sections.map((s) => [s.id, s]));

          // Check for new and updated sections
          for (const section of thesis.sections) {
            const initialSection = initialSections.get(section.id);

            if (!initialSection) {
              // New section
              const createdSection = await createSection(thesis.id);

              if (section.title !== "Untitled Section" || section.content) {
                await updateSection(thesis.id, createdSection.id, {
                  title: section.title,
                  content: section.content,
                });
              }

              // Add citations
              for (const citation of section.citations) {
                await addCitation(thesis.id, createdSection.id, citation.document_id);
              }
            } else {
              // Existing section - check for updates
              if (
                section.title !== initialSection.title ||
                section.content !== initialSection.content ||
                section.collapsed !== initialSection.collapsed
              ) {
                await updateSection(thesis.id, section.id, {
                  title: section.title,
                  content: section.content,
                  collapsed: section.collapsed,
                });
              }

              // Process citations
              const initialCitations = new Set(
                initialSection.citations.map((c) => c.document_id)
              );
              const currentCitations = new Set(
                section.citations.map((c) => c.document_id)
              );

              // Add new citations
              for (const citation of section.citations) {
                if (!initialCitations.has(citation.document_id)) {
                  await addCitation(thesis.id, section.id, citation.document_id);
                }
              }

              // Remove deleted citations
              for (const initialCitation of initialSection.citations) {
                if (!currentCitations.has(initialCitation.document_id)) {
                  await removeCitation(thesis.id, section.id, initialCitation.id);
                }
              }
            }
          }

          // Delete removed sections
          for (const initialSection of initial.sections) {
            if (!currentSections.has(initialSection.id)) {
              await deleteSection(thesis.id, initialSection.id);
            }
          }
        }
      }

      // Delete removed theses (if we add delete functionality)
      // for (const initial of initialTheses) {
      //   if (!currentMap.has(initial.id)) {
      //     await deleteThesis(initial.id);
      //   }
      // }

      // Reload from server to get server-generated IDs and sync state
      await loadTheses();
      showToast("All changes saved");
    } catch (error) {
      console.error("Failed to save changes:", error);
      showToast("Error saving changes");
    } finally {
      setSaving(false);
    }
  };

  // Save on page close
  useEffect(() => {
    const handleBeforeUnload = async (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        // Modern browsers ignore custom messages, just show generic warning
        e.preventDefault();
        e.returnValue = "";

        // Try to save (may not complete if page closes too fast)
        await saveAllChanges();
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [hasUnsavedChanges]);

  const showToast = (msg: string) => {
    setToast({ visible: true, message: msg });
    setTimeout(() => setToast({ visible: false, message: "" }), 2000);
  };

  // ===== Thesis CRUD =====

  const handleCreateThesis = () => {
    const newThesis: Thesis = {
      id: uuidv4(),
      title: "New Thesis",
      position: theses.length,
      sections: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setTheses((prev) => [...prev, newThesis]);
    setActiveThesisId(newThesis.id);
    showToast("Thesis created");
  };

  const handleUpdateThesis = (
    thesisId: string,
    update: { title?: string }
  ) => {
    setTheses((prev) =>
      prev.map((t) =>
        t.id === thesisId
          ? { ...t, ...update, updated_at: new Date().toISOString() }
          : t
      )
    );
  };

  // ===== Section CRUD =====

  const handleCreateSection = (thesisId: string) => {
    const thesis = theses.find((t) => t.id === thesisId);
    if (!thesis) return;

    const newSection = {
      id: uuidv4(),
      thesis_id: thesisId,
      title: "Untitled Section",
      content: "",
      position: thesis.sections.length,
      collapsed: false,
      citations: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setTheses((prev) =>
      prev.map((t) =>
        t.id === thesisId
          ? { ...t, sections: [...t.sections, newSection] }
          : t
      )
    );
    showToast("Section added");
  };

  const handleUpdateSection = (
    thesisId: string,
    sectionId: string,
    update: { title?: string; content?: string; collapsed?: boolean }
  ) => {
    setTheses((prev) =>
      prev.map((t) =>
        t.id === thesisId
          ? {
              ...t,
              sections: t.sections.map((s) =>
                s.id === sectionId
                  ? { ...s, ...update, updated_at: new Date().toISOString() }
                  : s
              ),
            }
          : t
      )
    );
  };

  const handleDeleteSection = (thesisId: string, sectionId: string) => {
    setTheses((prev) =>
      prev.map((t) =>
        t.id === thesisId
          ? { ...t, sections: t.sections.filter((s) => s.id !== sectionId) }
          : t
      )
    );
    showToast("Section deleted");
  };

  // ===== Citation Management =====

  const handleDrop = useCallback(
    (payload: any, toSectionId: string, toThesisId: string) => {
      const { citation, origin, fromSectionId } = payload;

      // Don't drop on self
      if (origin === "chip" && fromSectionId === toSectionId) return;

      setTheses((prev) => {
        return prev.map((thesis) => {
          if (thesis.id !== toThesisId && thesis.id !== payload.fromThesisId) {
            return thesis;
          }

          return {
            ...thesis,
            sections: thesis.sections.map((section) => {
              // Remove from source section if moving
              if (origin === "chip" && section.id === fromSectionId) {
                return {
                  ...section,
                  citations: section.citations.filter(
                    (c) => c.document_id !== citation.document_id
                  ),
                };
              }

              // Add to target section
              if (section.id === toSectionId) {
                // Check if already exists
                const exists = section.citations.some(
                  (c) => c.document_id === citation.document_id
                );
                if (exists) return section;

                return {
                  ...section,
                  citations: [
                    ...section.citations,
                    {
                      ...citation,
                      id: uuidv4(),
                      position: section.citations.length,
                    },
                  ],
                };
              }

              return section;
            }),
          };
        });
      });

      showToast(
        origin === "chip" ? "Citation moved" : "Citation added"
      );
    },
    []
  );

  const handleRemoveCitation = (
    thesisId: string,
    sectionId: string,
    citationId: string
  ) => {
    setTheses((prev) =>
      prev.map((t) =>
        t.id === thesisId
          ? {
              ...t,
              sections: t.sections.map((s) =>
                s.id === sectionId
                  ? {
                      ...s,
                      citations: s.citations.filter((c) => c.id !== citationId),
                    }
                  : s
              ),
            }
          : t
      )
    );
    showToast("Citation removed");
  };

  const { dragState, startDrag, registerZone } = useDragEngine(handleDrop);

  // ===== Chat Integration =====

  const handleAddSource = (source: Document) => {
    if (!activeThesisId) return;

    const thesis = theses.find((t) => t.id === activeThesisId);
    if (!thesis) return;

    setTheses((prev) =>
      prev.map((t) => {
        if (t.id !== activeThesisId) return t;

        const citation = {
          id: uuidv4(),
          title: source.title,
          sector: source.sector,
          sentiment: source.sentiment,
          summary: source.summary,
          document_id: source.id.toString(),
          position: 0,
        };

        // Add to last section or create new section
        if (t.sections.length === 0) {
          const newSection = {
            id: uuidv4(),
            thesis_id: activeThesisId,
            title: "Untitled Section",
            content: "",
            position: 0,
            collapsed: false,
            citations: [citation],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
          return { ...t, sections: [newSection] };
        } else {
          return {
            ...t,
            sections: t.sections.map((s, idx) =>
              idx === t.sections.length - 1
                ? {
                    ...s,
                    citations: [...s.citations, { ...citation, position: s.citations.length }],
                  }
                : s
            ),
          };
        }
      })
    );

    showToast("Source added");
  };

  const handleAddText = (text: string) => {
    if (!activeThesisId) return;

    const thesis = theses.find((t) => t.id === activeThesisId);
    if (!thesis) return;

    setTheses((prev) =>
      prev.map((t) => {
        if (t.id !== activeThesisId) return t;

        // Add to last section or create new section
        if (t.sections.length === 0) {
          const newSection = {
            id: uuidv4(),
            thesis_id: activeThesisId,
            title: "Untitled Section",
            content: text,
            position: 0,
            collapsed: false,
            citations: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
          return { ...t, sections: [newSection] };
        } else {
          return {
            ...t,
            sections: t.sections.map((s, idx) =>
              idx === t.sections.length - 1
                ? {
                    ...s,
                    content: s.content ? `${s.content}\n\n${text}` : text,
                    updated_at: new Date().toISOString(),
                  }
                : s
            ),
          };
        }
      })
    );

    showToast("Text added");
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-gray-400">Loading theses...</div>
      </div>
    );
  }

  return (
    <div
      style={{
        fontFamily: "'Georgia', serif",
        userSelect: dragState ? "none" : "auto",
      }}
      className="h-full flex overflow-hidden bg-gray-950"
    >
      {/* Chat Sidebar */}
      <ChatSidebar
        theses={theses}
        activeThesisId={activeThesisId}
        onAddSource={handleAddSource}
        onAddText={handleAddText}
        dragState={dragState}
        startDrag={startDrag}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-12 py-10">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <h1
                className="text-2xl font-bold text-gray-100"
                style={{ fontFamily: "'Georgia', serif" }}
              >
                Thesis Notebook
              </h1>
              {hasUnsavedChanges && (
                <span className="text-xs text-amber-600 font-medium">
                  (unsaved changes)
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {hasUnsavedChanges && (
                <button
                  onClick={saveAllChanges}
                  disabled={saving}
                  className="px-3 py-1.5 text-xs bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors font-medium"
                >
                  {saving ? "Saving..." : "Save"}
                </button>
              )}
              <button
                onClick={handleCreateThesis}
                className="px-3 py-1.5 text-xs bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors font-medium"
              >
                + New thesis
              </button>
            </div>
          </div>


          {theses.length === 0 ? (
            <div className="text-center py-20 text-gray-500">
              <p className="mb-2">No theses yet</p>
              <p className="text-xs text-gray-600">Click "+ New thesis" to get started</p>
            </div>
          ) : (
            theses.map((thesis) => (
              <ThesisBlock
                key={thesis.id}
                thesis={thesis}
                isActive={thesis.id === activeThesisId}
                onActivate={() => setActiveThesisId(thesis.id)}
                onUpdate={handleUpdateThesis}
                onAddSection={handleCreateSection}
                onDeleteSection={handleDeleteSection}
                onUpdateSection={handleUpdateSection}
                dragState={dragState}
                startDrag={startDrag}
                registerZone={registerZone}
              />
            ))
          )}
        </div>
      </div>

      {/* Drag Ghost */}
      <DragGhost dragState={dragState} />

      {/* Toast Notifications */}
      <Toast message={toast.message} visible={toast.visible} />
    </div>
  );
}
