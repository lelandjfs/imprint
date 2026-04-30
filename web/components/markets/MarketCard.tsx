/**
 * MarketCard - Bloomberg terminal-style market display
 */

"use client";

import { Market, MarketPrice, MarketAlignment } from "./types";

interface MarketCardProps {
  market: Market;
  price: MarketPrice | null;
  alignment?: {
    score: number;
    direction: "supports" | "contradicts" | "neutral";
    reasoning: string;
  };
}

export default function MarketCard({ market, price, alignment }: MarketCardProps) {
  // Price color based on probability
  const priceColor = price
    ? price.yes_price > 0.5
      ? "text-emerald-400"
      : price.yes_price < 0.5
      ? "text-red-400"
      : "text-gray-400"
    : "text-gray-500";

  // Alignment direction badge styling
  const directionStyles = {
    supports: "bg-emerald-900/30 text-emerald-400 border-emerald-700/50",
    contradicts: "bg-red-900/30 text-red-400 border-red-700/50",
    neutral: "bg-gray-800/50 text-gray-400 border-gray-700/50",
  };

  // Platform badge color
  const platformColor = market.platform === "kalshi" ? "text-blue-400" : "text-purple-400";

  // Format large numbers
  const formatVolume = (vol: number | null) => {
    if (!vol) return "";
    if (vol >= 1_000_000) return `$${(vol / 1_000_000).toFixed(1)}M`;
    if (vol >= 1_000) return `$${(vol / 1_000).toFixed(1)}K`;
    return `$${vol.toFixed(0)}`;
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded hover:border-gray-700 transition-colors">
      <div className="p-4">
        {/* Header: Title + Platform */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 pr-4">
            <h3 className="font-medium text-gray-100 text-sm leading-tight mb-1.5">
              {market.title}
            </h3>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className={`uppercase font-mono font-medium ${platformColor}`}>
                {market.platform}
              </span>
              {market.category && (
                <>
                  <span className="text-gray-700">|</span>
                  <span>{market.category}</span>
                </>
              )}
            </div>
          </div>

          {/* Current Price */}
          <div className="text-right shrink-0">
            <div className={`font-mono text-2xl font-medium ${priceColor}`}>
              {price ? `${(price.yes_price * 100).toFixed(0)}%` : "--"}
            </div>
            {price?.volume_24h && (
              <div className="text-xs text-gray-500 font-mono mt-0.5">
                {formatVolume(price.volume_24h)} vol
              </div>
            )}
          </div>
        </div>

        {/* Description (if available) */}
        {market.description && (
          <p className="text-xs text-gray-400 leading-relaxed mb-3 line-clamp-2">
            {market.description}
          </p>
        )}

        {/* Alignment (if provided) */}
        {alignment && (
          <div className="mt-3 pt-3 border-t border-gray-800">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`px-2 py-0.5 text-xs font-medium font-mono rounded border ${
                  directionStyles[alignment.direction]
                }`}
              >
                {alignment.direction.toUpperCase()}
              </span>
              <span className="font-mono text-sm text-gray-400">
                {(alignment.score * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              {alignment.reasoning}
            </p>
          </div>
        )}

        {/* Trade Link */}
        <a
          href={market.market_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 block text-center py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-medium font-mono rounded transition-colors"
        >
          TRADE ON {market.platform.toUpperCase()}
        </a>
      </div>
    </div>
  );
}
