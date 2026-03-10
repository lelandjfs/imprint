"use client";

import { Document } from "@/lib/types";

interface SourcesPanelProps {
  sources: Document[];
  isOpen: boolean;
  onClose: () => void;
}

export default function SourcesPanel({
  sources,
  isOpen,
  onClose,
}: SourcesPanelProps) {
  if (!isOpen) return null;

  return (
    <div className="w-80 border-l border-gray-200 p-4 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">
          Sources ({sources.length})
        </h2>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
      </div>

      <div className="space-y-4">
        {sources.map((doc) => (
          <div
            key={doc.id}
            className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50"
          >
            <h3 className="font-medium text-sm mb-2">{doc.title}</h3>

            {doc.summary && (
              <p className="text-xs text-gray-600 mb-2">{doc.summary}</p>
            )}

            <div className="flex flex-wrap gap-1 mb-2">
              {doc.sector && (
                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                  {doc.sector}
                </span>
              )}
              {doc.sentiment && (
                <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                  {doc.sentiment}
                </span>
              )}
              {doc.document_type && (
                <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">
                  {doc.document_type}
                </span>
              )}
            </div>

            {doc.entities && doc.entities.length > 0 && (
              <div className="text-xs text-gray-500 mb-2">
                {doc.entities.slice(0, 3).join(", ")}
                {doc.entities.length > 3 && ` +${doc.entities.length - 3}`}
              </div>
            )}

            {doc.source_url && (
              <a
                href={doc.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:underline"
              >
                View source →
              </a>
            )}

            <div className="text-xs text-gray-400 mt-2">
              Similarity: {(doc.similarity * 100).toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
