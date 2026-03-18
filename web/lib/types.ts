/**
 * Type definitions for Imprint Chat
 */

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Document[];
}

export interface DocumentAnalysis {
  summary: string;
  key_excerpt: string;
  thesis_signal: "bullish" | "bearish" | "neutral" | "mixed";
  thesis_utility: string;
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
  analysis?: DocumentAnalysis;
}

export interface ChatFilters {
  sector?: string[] | null;
  entities?: string[] | null;
  sentiment?: string[] | null;
  catalyst_window?: string[] | null;
  weighting?: number[] | null;
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
  weighting: number[];
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
}

export interface QueryAnalysis {
  topic: string | null;
  entities: string[];
  sectors: string[];
  sentiment_intent: string | null;
  catalyst_window: string | null;
  search_intent: string;
}

export interface StreamEvent {
  type: "sources" | "token" | "done" | "error" | "query_analysis" | "run_id";
  documents?: Document[];
  content?: string;
  full_response?: string;
  message?: string;
  analysis?: QueryAnalysis;
  run_id?: string;
}

// ========== Thesis Types ==========

export interface ThesisCitation {
  id: string;
  title: string;
  sector: string | null;
  sentiment: string | null;
  summary: string | null;
  document_id: string;
  position: number;
}

export interface ThesisSection {
  id: string;
  thesis_id: string;
  title: string;
  content: string;
  position: number;
  collapsed: boolean;
  citations: ThesisCitation[];
  created_at: string;
  updated_at: string;
}

export interface Thesis {
  id: string;
  title: string;
  position: number;
  sections: ThesisSection[];
  created_at: string;
  updated_at: string;
}

export interface DragPayload {
  citation: ThesisCitation;
  origin: "chip" | "sidebar";
  fromSectionId: string | null;
  fromThesisId: string | null;
}

export interface DragState {
  payload: DragPayload;
  x: number;
  y: number;
  overZoneId: string | null;
}
