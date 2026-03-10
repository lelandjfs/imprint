/**
 * Type definitions for Imprint Chat
 */

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Document[];
}

export interface Document {
  id: number;
  title: string;
  summary: string | null;
  topic: string | null;
  sector: string | null;
  entities: string[] | null;
  sentiment: string | null;
  document_type: string | null;
  catalyst_window: string | null;
  weighting: number | null;
  source_url: string | null;
  similarity: number;
}

export interface ChatFilters {
  sector?: string[] | null;
  entities?: string[] | null;
  sentiment?: string[] | null;
  date_range?: {
    start?: string | null;
    end?: string | null;
  };
}

export interface FilterOptions {
  sector: string[];
  entities: string[];
  sentiment: string[];
  document_type: string[];
  catalyst_window: string[];
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
}

export interface StreamEvent {
  type: "sources" | "token" | "done" | "error";
  documents?: Document[];
  content?: string;
  full_response?: string;
  message?: string;
}
