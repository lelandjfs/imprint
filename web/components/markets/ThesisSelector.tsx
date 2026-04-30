/**
 * ThesisSelector - Dropdown to select a thesis for alignment view
 */

"use client";

interface Thesis {
  id: string;
  title: string;
}

interface ThesisSelectorProps {
  theses: Thesis[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}

export default function ThesisSelector({
  theses,
  selectedId,
  onSelect,
}: ThesisSelectorProps) {
  return (
    <select
      value={selectedId || ""}
      onChange={(e) => onSelect(e.target.value || null)}
      className="bg-gray-900 border border-gray-800 text-gray-300 text-sm font-mono rounded px-3 py-1.5 focus:outline-none focus:border-gray-700"
    >
      <option value="">Select thesis...</option>
      {theses.map((thesis) => (
        <option key={thesis.id} value={thesis.id}>
          {thesis.title}
        </option>
      ))}
    </select>
  );
}
