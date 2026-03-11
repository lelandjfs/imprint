"use client";

import { useState } from "react";
import { ChatFilters, FilterOptions } from "@/lib/types";
import { ChevronDownIcon, ChevronUpIcon } from "./Icons";

interface FilterSidebarProps {
  filters: ChatFilters;
  filterOptions: FilterOptions | null;
  onFiltersChange: (filters: ChatFilters) => void;
  onClear: () => void;
}

export default function FilterSidebarModern({
  filters,
  filterOptions,
  onFiltersChange,
  onClear,
}: FilterSidebarProps) {
  const [expandedSections, setExpandedSections] = useState({
    sector: true,
    sentiment: true,
    entities: false,
    catalyst_window: false,
    weighting: false,
  });

  const [entitySearch, setEntitySearch] = useState("");

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const handleSectorChange = (sector: string) => {
    const currentSectors = filters.sector || [];
    const newSectors = currentSectors.includes(sector)
      ? currentSectors.filter((s) => s !== sector)
      : [...currentSectors, sector];
    onFiltersChange({ ...filters, sector: newSectors.length > 0 ? newSectors : null });
  };

  const handleSentimentChange = (sentiment: string) => {
    const currentSentiments = filters.sentiment || [];
    const newSentiments = currentSentiments.includes(sentiment)
      ? currentSentiments.filter((s) => s !== sentiment)
      : [...currentSentiments, sentiment];
    onFiltersChange({
      ...filters,
      sentiment: newSentiments.length > 0 ? newSentiments : null,
    });
  };

  const handleEntityChange = (entity: string) => {
    const currentEntities = filters.entities || [];
    const newEntities = currentEntities.includes(entity)
      ? currentEntities.filter((e) => e !== entity)
      : [...currentEntities, entity];
    onFiltersChange({
      ...filters,
      entities: newEntities.length > 0 ? newEntities : null,
    });
  };

  const handleCatalystChange = (catalyst: string) => {
    const currentCatalysts = filters.catalyst_window || [];
    const newCatalysts = currentCatalysts.includes(catalyst)
      ? currentCatalysts.filter((c) => c !== catalyst)
      : [...currentCatalysts, catalyst];
    onFiltersChange({
      ...filters,
      catalyst_window: newCatalysts.length > 0 ? newCatalysts : null,
    });
  };

  const handleWeightingChange = (weight: number) => {
    const currentWeights = filters.weighting || [];
    const newWeights = currentWeights.includes(weight)
      ? currentWeights.filter((w) => w !== weight)
      : [...currentWeights, weight];
    onFiltersChange({
      ...filters,
      weighting: newWeights.length > 0 ? newWeights : null,
    });
  };

  const activeFilterCount = [
    filters.sector?.length,
    filters.sentiment?.length,
    filters.entities?.length,
    filters.catalyst_window?.length,
    filters.weighting?.length,
  ].filter(Boolean).length;

  // Filter entities by search
  const filteredEntities = filterOptions?.entities.filter((entity) =>
    entity.toLowerCase().includes(entitySearch.toLowerCase())
  ) || [];

  return (
    <div className="w-80 border-r border-gray-200 bg-gray-50 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 p-4 z-10">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Filters
            {activeFilterCount > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-blue-600 text-white text-xs rounded-full">
                {activeFilterCount}
              </span>
            )}
          </h2>
          <button
            onClick={onClear}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Clear all
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Sector */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection("sector")}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">
              Sector
              {filters.sector && filters.sector.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                  {filters.sector.length}
                </span>
              )}
            </span>
            {expandedSections.sector ? (
              <ChevronUpIcon className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDownIcon className="w-5 h-5 text-gray-400" />
            )}
          </button>
          {expandedSections.sector && (
            <div className="p-3 pt-0 border-t border-gray-100 space-y-2">
              {filterOptions?.sector.map((sector) => (
                <label
                  key={sector}
                  className="flex items-center text-sm hover:bg-gray-50 p-1 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={filters.sector?.includes(sector) || false}
                    onChange={() => handleSectorChange(sector)}
                    className="mr-2 rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700">{sector}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Sentiment */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection("sentiment")}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">
              Sentiment
              {filters.sentiment && filters.sentiment.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                  {filters.sentiment.length}
                </span>
              )}
            </span>
            {expandedSections.sentiment ? (
              <ChevronUpIcon className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDownIcon className="w-5 h-5 text-gray-400" />
            )}
          </button>
          {expandedSections.sentiment && (
            <div className="p-3 pt-0 border-t border-gray-100 space-y-2">
              {filterOptions?.sentiment.map((sentiment) => (
                <label
                  key={sentiment}
                  className="flex items-center text-sm hover:bg-gray-50 p-1 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={filters.sentiment?.includes(sentiment) || false}
                    onChange={() => handleSentimentChange(sentiment)}
                    className="mr-2 rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700 capitalize">{sentiment}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Entities */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection("entities")}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">
              Entities
              {filters.entities && filters.entities.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                  {filters.entities.length}
                </span>
              )}
            </span>
            {expandedSections.entities ? (
              <ChevronUpIcon className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDownIcon className="w-5 h-5 text-gray-400" />
            )}
          </button>
          {expandedSections.entities && (
            <div className="border-t border-gray-100">
              <div className="p-3">
                <input
                  type="text"
                  placeholder="Search entities..."
                  value={entitySearch}
                  onChange={(e) => setEntitySearch(e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="px-3 pb-3 space-y-2 max-h-64 overflow-y-auto">
                {filteredEntities.length === 0 ? (
                  <div className="text-sm text-gray-500 text-center py-2">
                    No entities match &quot;{entitySearch}&quot;
                  </div>
                ) : (
                  filteredEntities.map((entity) => (
                    <label
                      key={entity}
                      className="flex items-center text-sm hover:bg-gray-50 p-1 rounded cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={filters.entities?.includes(entity) || false}
                        onChange={() => handleEntityChange(entity)}
                        className="mr-2 rounded text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-gray-700">{entity}</span>
                    </label>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Catalyst Window */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection("catalyst_window")}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">
              Catalyst Window
              {filters.catalyst_window && filters.catalyst_window.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                  {filters.catalyst_window.length}
                </span>
              )}
            </span>
            {expandedSections.catalyst_window ? (
              <ChevronUpIcon className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDownIcon className="w-5 h-5 text-gray-400" />
            )}
          </button>
          {expandedSections.catalyst_window && (
            <div className="p-3 pt-0 border-t border-gray-100 space-y-2">
              {filterOptions?.catalyst_window.map((catalyst) => (
                <label
                  key={catalyst}
                  className="flex items-center text-sm hover:bg-gray-50 p-1 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={filters.catalyst_window?.includes(catalyst) || false}
                    onChange={() => handleCatalystChange(catalyst)}
                    className="mr-2 rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700 capitalize">{catalyst.replace(/_/g, ' ')}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Weighting */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection("weighting")}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">
              Weighting
              {filters.weighting && filters.weighting.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                  {filters.weighting.length}
                </span>
              )}
            </span>
            {expandedSections.weighting ? (
              <ChevronUpIcon className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDownIcon className="w-5 h-5 text-gray-400" />
            )}
          </button>
          {expandedSections.weighting && (
            <div className="p-3 pt-0 border-t border-gray-100 space-y-2">
              {filterOptions?.weighting.map((weight) => (
                <label
                  key={weight}
                  className="flex items-center text-sm hover:bg-gray-50 p-1 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={filters.weighting?.includes(weight) || false}
                    onChange={() => handleWeightingChange(weight)}
                    className="mr-2 rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700">⭐ {weight}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
