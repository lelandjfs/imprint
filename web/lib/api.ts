/**
 * API client for Imprint Chat backend
 */

import {
  ChatFilters,
  FilterOptions,
  ModelInfo,
  StreamEvent,
  Thesis,
  ThesisSection,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Stream chat responses from the API
 */
export async function* streamChat(
  sessionId: string,
  message: string,
  model: string,
  filters?: ChatFilters
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      model,
      filters,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        try {
          const event: StreamEvent = JSON.parse(data);
          yield event;
        } catch (e) {
          console.error("Failed to parse SSE data:", e);
        }
      }
    }
  }
}

/**
 * Get available filter options
 */
export async function getFilters(): Promise<FilterOptions> {
  const response = await fetch(`${API_URL}/api/filters`);
  if (!response.ok) {
    throw new Error(`Failed to fetch filters: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get available models
 */
export async function getModels(): Promise<{
  models: ModelInfo[];
  default: string;
}> {
  const response = await fetch(`${API_URL}/api/models`);
  if (!response.ok) {
    throw new Error(`Failed to fetch models: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Clear conversation history
 */
export async function clearSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to clear session: ${response.statusText}`);
  }
}

// ========== Thesis API Functions ==========

/**
 * Get all theses with nested sections and citations
 */
export async function getTheses(): Promise<{ theses: Thesis[] }> {
  const response = await fetch(`${API_URL}/api/theses`);
  if (!response.ok) {
    throw new Error(`Failed to fetch theses: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Create a new thesis
 */
export async function createThesis(title: string): Promise<Thesis> {
  const response = await fetch(`${API_URL}/api/theses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create thesis: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Update thesis (auto-save)
 */
export async function updateThesis(
  thesisId: string,
  update: { title?: string; position?: number }
): Promise<void> {
  const response = await fetch(`${API_URL}/api/theses/${thesisId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
  if (!response.ok) {
    throw new Error(`Failed to update thesis: ${response.statusText}`);
  }
}

/**
 * Delete thesis
 */
export async function deleteThesis(thesisId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/theses/${thesisId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete thesis: ${response.statusText}`);
  }
}

/**
 * Create section
 */
export async function createSection(
  thesisId: string,
  title: string = "New Section"
): Promise<ThesisSection> {
  const response = await fetch(`${API_URL}/api/theses/${thesisId}/sections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create section: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Update section (auto-save)
 */
export async function updateSection(
  thesisId: string,
  sectionId: string,
  update: { title?: string; content?: string; collapsed?: boolean }
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/theses/${thesisId}/sections/${sectionId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
    }
  );
  if (!response.ok) {
    throw new Error(`Failed to update section: ${response.statusText}`);
  }
}

/**
 * Delete section
 */
export async function deleteSection(
  thesisId: string,
  sectionId: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/theses/${thesisId}/sections/${sectionId}`,
    {
      method: "DELETE",
    }
  );
  if (!response.ok) {
    throw new Error(`Failed to delete section: ${response.statusText}`);
  }
}

/**
 * Add citation to section
 */
export async function addCitation(
  thesisId: string,
  sectionId: string,
  documentId: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/theses/${thesisId}/sections/${sectionId}/citations`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId }),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to add citation");
  }
}

/**
 * Remove citation from section
 */
export async function removeCitation(
  thesisId: string,
  sectionId: string,
  citationId: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/theses/${thesisId}/sections/${sectionId}/citations/${citationId}`,
    { method: "DELETE" }
  );
  if (!response.ok) {
    throw new Error(`Failed to remove citation: ${response.statusText}`);
  }
}

/**
 * Move citation between sections
 */
export async function moveCitation(
  thesisId: string,
  toSectionId: string,
  fromSectionId: string,
  documentId: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/theses/${thesisId}/sections/${toSectionId}/citations/move?from_section_id=${fromSectionId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId }),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to move citation");
  }
}
