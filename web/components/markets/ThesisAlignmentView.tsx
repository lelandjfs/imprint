/**
 * ThesisAlignmentView - Markets aligned to a specific thesis
 */

"use client";

import { useState, useEffect } from "react";
import MarketCard from "./MarketCard";
import { MarketThesisItem } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ThesisAlignmentViewProps {
  thesisId: string | null;
}

export default function ThesisAlignmentView({ thesisId }: ThesisAlignmentViewProps) {
  const [markets, setMarkets] = useState<MarketThesisItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (thesisId) {
      fetchThesisMarkets(thesisId);
    } else {
      setMarkets([]);
    }
  }, [thesisId]);

  const fetchThesisMarkets = async (id: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/markets/thesis/${id}?limit=20`);
      if (!response.ok) {
        throw new Error("Failed to fetch markets");
      }

      const data = await response.json();
      setMarkets(data.markets || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  if (!thesisId) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-gray-500 font-mono text-sm">
          Select a thesis to view aligned markets
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-gray-500 font-mono text-sm">Loading markets...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-red-400 font-mono text-sm">Error: {error}</div>
      </div>
    );
  }

  if (markets.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <div className="text-gray-500 font-mono text-sm mb-2">
          No aligned markets found
        </div>
        <div className="text-gray-600 text-xs">
          Markets will appear here once alignments are computed
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-lg font-medium text-gray-100 mb-1">
            Aligned Markets
          </h2>
          <p className="text-sm text-gray-500">
            {markets.length} market{markets.length !== 1 ? "s" : ""} aligned to this thesis
          </p>
        </div>

        {/* Market Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {markets.map((market) => (
            <MarketCard
              key={market.id}
              market={market}
              price={market.current_price}
              alignment={{
                score: market.alignment_score,
                direction: market.alignment_direction,
                reasoning: market.reasoning,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
