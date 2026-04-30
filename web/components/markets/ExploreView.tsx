/**
 * ExploreView - "For You" page showing markets ranked by global relevance
 */

"use client";

import { useState, useEffect } from "react";
import MarketCard from "./MarketCard";
import { MarketExploreItem } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ExploreView() {
  const [markets, setMarkets] = useState<MarketExploreItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchExploreMarkets();
  }, []);

  const fetchExploreMarkets = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/markets/explore?limit=20`);
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
        <div className="text-gray-500 font-mono text-sm mb-2">No markets found</div>
        <div className="text-gray-600 text-xs">
          Markets will appear here once thesis alignments are computed
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
            Markets For You
          </h2>
          <p className="text-sm text-gray-500">
            Ranked by relevance across all your theses
          </p>
        </div>

        {/* Market Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {markets.map((market) => {
            // Get highest alignment for display
            const topAlignment = market.top_alignments[0];

            return (
              <MarketCard
                key={market.id}
                market={market}
                price={market.current_price}
                alignment={
                  topAlignment
                    ? {
                        score: topAlignment.alignment_score,
                        direction: topAlignment.alignment_direction,
                        reasoning: topAlignment.reasoning,
                      }
                    : undefined
                }
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
