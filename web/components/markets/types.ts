/**
 * TypeScript interfaces for Markets feature
 */

export interface Market {
  id: string;
  platform: "kalshi" | "polymarket";
  external_id: string;
  title: string;
  description: string | null;
  category: string | null;
  end_date: string | null;
  status: "active" | "closed" | "resolved";
  market_url: string;
}

export interface MarketPrice {
  yes_price: number;
  no_price: number | null;
  volume_24h: number | null;
  open_interest: number | null;
  fetched_at: string;
}

export interface MarketPricePoint {
  timestamp: string;
  price: number;
  volume: number | null;
}

export interface MarketWithPrice extends Market {
  current_price: MarketPrice | null;
  price_history: MarketPricePoint[] | null;
}

export interface ThesisInfo {
  id: string;
  title: string;
}

export interface MarketAlignment {
  thesis: ThesisInfo;
  alignment_score: number;
  alignment_direction: "supports" | "contradicts" | "neutral";
  reasoning: string;
}

export interface MarketExploreItem extends Market {
  current_price: MarketPrice | null;
  relevance_score: number;
  top_alignments: MarketAlignment[];
}

export interface MarketThesisItem extends Market {
  current_price: MarketPrice | null;
  alignment_score: number;
  alignment_direction: "supports" | "contradicts" | "neutral";
  reasoning: string;
}
