/**
 * API client for Imprint Chat backend
 */

import { ChatFilters, FilterOptions, ModelInfo, StreamEvent } from "./types";

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
