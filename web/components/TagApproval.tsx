"use client";

import { useState, useEffect } from "react";

interface PendingDocument {
  id: string;
  title: string;
  source_type: string;
  thesis: string;
  topic: string;
  sector: string;
  entities: string[];
  summary: string;
  content: string;
  ingested_date: string;
}

export default function TagApproval() {
  const [documents, setDocuments] = useState<PendingDocument[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<PendingDocument | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPendingDocuments();
  }, []);

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

  const approveDocument = async (docId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/documents/${docId}/approve`,
        { method: "POST" }
      );
      if (response.ok) {
        setDocuments(documents.filter((d) => d.id !== docId));
        setSelectedDoc(null);
      }
    } catch (error) {
      console.error("Failed to approve document:", error);
    }
  };

  const rejectDocument = async (docId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/documents/${docId}/reject`,
        { method: "POST" }
      );
      if (response.ok) {
        setDocuments(documents.filter((d) => d.id !== docId));
        setSelectedDoc(null);
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
                  {doc.source_type} • {new Date(doc.ingested_date).toLocaleDateString()}
                </div>
                <div className="flex flex-wrap gap-1">
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
                    {doc.sector}
                  </span>
                  <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded">
                    {doc.thesis}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Document Detail */}
      <div className="flex-1 overflow-y-auto">
        {selectedDoc ? (
          <div className="p-8">
            <div className="max-w-4xl mx-auto">
              <h1 className="text-2xl font-bold text-gray-900 mb-4">
                {selectedDoc.title}
              </h1>

              {/* Metadata */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Source:</span>{" "}
                    <span className="text-gray-600">{selectedDoc.source_type}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Sector:</span>{" "}
                    <span className="text-gray-600">{selectedDoc.sector}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Thesis:</span>{" "}
                    <span className="text-gray-600">{selectedDoc.thesis}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Topic:</span>{" "}
                    <span className="text-gray-600">{selectedDoc.topic}</span>
                  </div>
                </div>
                <div className="mt-3">
                  <span className="font-medium text-gray-700 text-sm">Entities:</span>{" "}
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedDoc.entities?.map((entity) => (
                      <span
                        key={entity}
                        className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded"
                      >
                        {entity}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Summary */}
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 mb-2">Summary</h3>
                <p className="text-gray-700">{selectedDoc.summary}</p>
              </div>

              {/* Content Preview */}
              <div className="mb-8">
                <h3 className="font-semibold text-gray-900 mb-2">Content</h3>
                <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                  {selectedDoc.content.slice(0, 2000)}
                  {selectedDoc.content.length > 2000 && "..."}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 sticky bottom-0 bg-white py-4 border-t border-gray-200">
                <button
                  onClick={() => approveDocument(selectedDoc.id)}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  ✓ Approve
                </button>
                <button
                  onClick={() => rejectDocument(selectedDoc.id)}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  ✗ Reject
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
