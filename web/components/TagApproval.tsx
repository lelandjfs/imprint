"use client";

import { useState, useEffect, useRef } from "react";

interface PendingDocument {
  id: string;
  title: string;
  source_type: string;
  topic: string | null;
  sector: string | null;
  entities: string[];
  sentiment: string | null;
  document_type: string | null;
  catalyst_window: string | null;
  summary: string | null;
  weighting: number | null;
  content: string;
  source_url: string | null;
  ingested_date: string;
}

type SaveStatus = "idle" | "saving" | "saved" | "error";

const SECTOR_OPTIONS = [
  "Infra",
  "Software",
  "Semiconductors",
  "Security",
  "Fintech",
  "Healthcare",
  "Energy",
  "Industrial",
  "Consumer",
  "Macro",
  "Government",
  "Geopolitics",
];

const SENTIMENT_OPTIONS = ["bullish", "bearish", "neutral", "mixed"];

const DOCUMENT_TYPE_OPTIONS = [
  "memo",
  "article",
  "research_report",
  "transcript",
  "presentation",
  "other",
];

const CATALYST_WINDOW_OPTIONS = [
  "immediate",
  "near_term",
  "medium_term",
  "long_term",
  "structural",
];

export default function TagApproval() {
  const [documents, setDocuments] = useState<PendingDocument[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<PendingDocument | null>(null);
  const [editedDoc, setEditedDoc] = useState<PendingDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [newEntity, setNewEntity] = useState("");
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchPendingDocuments();
  }, []);

  useEffect(() => {
    setEditedDoc(selectedDoc);
  }, [selectedDoc]);

  const fetchPendingDocuments = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/documents/pending`
      );
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (error) {
      console.error("Failed to fetch pending documents:", error);
    } finally {
      setLoading(false);
    }
  };

  const autoSaveField = async (field: string, value: any) => {
    if (!editedDoc) return;

    setSaveStatus("saving");
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/documents/${editedDoc.id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [field]: value }),
        }
      );

      if (response.ok) {
        setSaveStatus("saved");
        setTimeout(() => setSaveStatus("idle"), 2000);
      } else {
        setSaveStatus("error");
      }
    } catch (error) {
      console.error("Failed to save field:", error);
      setSaveStatus("error");
    }
  };

  const handleFieldChange = (field: string, value: any) => {
    if (!editedDoc) return;

    setEditedDoc({ ...editedDoc, [field]: value });

    // Debounce auto-save (1 second)
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    saveTimeoutRef.current = setTimeout(() => {
      autoSaveField(field, value);
    }, 1000);
  };

  const addEntity = () => {
    if (!editedDoc || !newEntity.trim()) return;

    const updatedEntities = [...editedDoc.entities, newEntity.trim()];
    setEditedDoc({ ...editedDoc, entities: updatedEntities });
    setNewEntity("");
    autoSaveField("entities", updatedEntities);
  };

  const removeEntity = (entity: string) => {
    if (!editedDoc) return;

    const updatedEntities = editedDoc.entities.filter((e) => e !== entity);
    setEditedDoc({ ...editedDoc, entities: updatedEntities });
    autoSaveField("entities", updatedEntities);
  };

  const approveDocument = async (docId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/documents/${docId}/approve`,
        { method: "POST" }
      );
      if (response.ok) {
        setDocuments(documents.filter((d) => d.id !== docId));
        setSelectedDoc(null);
        setEditedDoc(null);
      }
    } catch (error) {
      console.error("Failed to approve document:", error);
    }
  };

  const rejectDocument = async (docId: string) => {
    if (
      !confirm(
        "Delete document and source file from Gmail/Drive? This cannot be undone."
      )
    )
      return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/documents/${docId}?delete_source=true`,
        { method: "DELETE" }
      );
      if (response.ok) {
        setDocuments(documents.filter((d) => d.id !== docId));
        setSelectedDoc(null);
        setEditedDoc(null);
      }
    } catch (error) {
      console.error("Failed to reject document:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Loading pending documents...</div>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Document List */}
      <div className="w-96 border-r border-gray-200 overflow-y-auto">
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-900">
            Pending Review ({documents.length})
          </h2>
        </div>
        <div className="divide-y divide-gray-200">
          {documents.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No documents pending review
            </div>
          ) : (
            documents.map((doc) => (
              <button
                key={doc.id}
                onClick={() => setSelectedDoc(doc)}
                className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                  selectedDoc?.id === doc.id ? "bg-blue-50" : ""
                }`}
              >
                <div className="font-medium text-gray-900 mb-1 line-clamp-2">
                  {doc.title}
                </div>
                <div className="text-sm text-gray-500 mb-2">
                  {doc.source_type} •{" "}
                  {new Date(doc.ingested_date).toLocaleDateString()}
                </div>
                <div className="flex flex-wrap gap-1">
                  {doc.sector && (
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
                      {doc.sector}
                    </span>
                  )}
                  {doc.sentiment && (
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded">
                      {doc.sentiment}
                    </span>
                  )}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Document Detail */}
      <div className="flex-1 overflow-y-auto">
        {editedDoc ? (
          <div className="p-8">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold text-gray-900">
                  {editedDoc.title}
                </h1>
                {saveStatus !== "idle" && (
                  <div className="text-sm">
                    {saveStatus === "saving" && (
                      <span className="text-blue-600">Saving...</span>
                    )}
                    {saveStatus === "saved" && (
                      <span className="text-green-600">✓ Saved</span>
                    )}
                    {saveStatus === "error" && (
                      <span className="text-red-600">✗ Error</span>
                    )}
                  </div>
                )}
              </div>

              {/* Editable Fields - Compact 2-column grid */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="grid grid-cols-2 gap-4">
                  {/* Topic */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Topic <span className="text-gray-400 text-xs">(snake_case)</span>
                    </label>
                    <input
                      type="text"
                      value={editedDoc.topic || ""}
                      onChange={(e) => handleFieldChange("topic", e.target.value)}
                      placeholder="e.g. ai_infrastructure"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    />
                  </div>

                  {/* Sector */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Sector
                    </label>
                    <select
                      value={editedDoc.sector || ""}
                      onChange={(e) => handleFieldChange("sector", e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                      <option value="">Select sector...</option>
                      {SECTOR_OPTIONS.map((sector) => (
                        <option key={sector} value={sector}>
                          {sector}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Sentiment */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Sentiment
                    </label>
                    <select
                      value={editedDoc.sentiment || ""}
                      onChange={(e) => handleFieldChange("sentiment", e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                      <option value="">Select sentiment...</option>
                      {SENTIMENT_OPTIONS.map((sentiment) => (
                        <option key={sentiment} value={sentiment}>
                          {sentiment}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Document Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Document Type
                    </label>
                    <select
                      value={editedDoc.document_type || ""}
                      onChange={(e) => handleFieldChange("document_type", e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                      <option value="">Select document type...</option>
                      {DOCUMENT_TYPE_OPTIONS.map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Catalyst Window */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Catalyst Window <span className="text-gray-400 text-xs">(optional)</span>
                    </label>
                    <select
                      value={editedDoc.catalyst_window || ""}
                      onChange={(e) => handleFieldChange("catalyst_window", e.target.value || null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                      <option value="">None</option>
                      {CATALYST_WINDOW_OPTIONS.map((window) => (
                        <option key={window} value={window}>
                          {window}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Weighting - spans 2 columns */}
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Weighting <span className="text-gray-400 text-xs">(optional)</span>
                    </label>
                    <div className="flex gap-2">
                      {[1, 2, 3, 4, 5].map((weight) => (
                        <button
                          key={weight}
                          onClick={() => handleFieldChange("weighting", weight)}
                          className={`w-10 h-10 rounded-md font-medium transition-colors text-sm ${
                            editedDoc.weighting === weight
                              ? "bg-blue-600 text-white"
                              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                          }`}
                        >
                          {weight}
                        </button>
                      ))}
                      <button
                        onClick={() => handleFieldChange("weighting", null)}
                        className="px-3 h-10 rounded-md bg-gray-200 text-gray-700 hover:bg-gray-300 text-sm"
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                </div>

                {/* Entities - Full width outside grid */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Entities
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {editedDoc.entities.map((entity) => (
                      <span
                        key={entity}
                        className="inline-flex items-center gap-1 px-2 py-1 bg-gray-200 text-gray-700 text-sm rounded"
                      >
                        {entity}
                        <button
                          onClick={() => removeEntity(entity)}
                          className="text-gray-500 hover:text-red-600"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newEntity}
                      onChange={(e) => setNewEntity(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && addEntity()}
                      placeholder="Add entity (press Enter)"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <button
                      onClick={addEntity}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Add
                    </button>
                  </div>
                </div>

                {/* Summary - Full width outside grid */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Summary <span className="text-gray-400 text-xs">(one sentence)</span>
                  </label>
                  <textarea
                    value={editedDoc.summary || ""}
                    onChange={(e) => handleFieldChange("summary", e.target.value)}
                    rows={3}
                    placeholder="One sentence takeaway..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  />
                </div>
              </div>

              {/* Content Preview */}
              <div className="mb-8">
                <h3 className="font-semibold text-gray-900 mb-2">Content Preview</h3>
                <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap bg-gray-50 rounded-lg p-4">
                  {editedDoc.content.slice(0, 2000)}
                  {editedDoc.content.length > 2000 && "..."}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 sticky bottom-0 bg-white py-4 border-t border-gray-200">
                <button
                  onClick={() => approveDocument(editedDoc.id)}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  ✓ Approve
                </button>
                <button
                  onClick={() => rejectDocument(editedDoc.id)}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  ✗ Reject & Delete Source
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            Select a document to review
          </div>
        )}
      </div>
    </div>
  );
}
