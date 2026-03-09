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
    thesis: true,
    sector: true,
    entities: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const handleThesisChange = (thesis: string) => {
    const currentTheses = filters.thesis || [];
    const newTheses = currentTheses.includes(thesis)
      ? currentTheses.filter((t) => t !== thesis)
      : [...currentTheses, thesis];
    onFiltersChange({ ...filters, thesis: newTheses.length > 0 ? newTheses : null });
  };

  const handleSectorChange = (sector: string) => {
    const currentSectors = filters.sector || [];
    const newSectors = currentSectors.includes(sector)
      ? currentSectors.filter((s) => s !== sector)
      : [...currentSectors, sector];
    onFiltersChange({ ...filters, sector: newSectors.length > 0 ? newSectors : null });
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

  const activeFilterCount = [
    filters.thesis?.length,
    filters.sector?.length,
    filters.entities?.length,
  ].filter(Boolean).length;

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
        {/* Thesis */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection("thesis")}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">
              Thesis
              {filters.thesis && filters.thesis.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                  {filters.thesis.length}
                </span>
              )}
            </span>
            {expandedSections.thesis ? (
              <ChevronUpIcon className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDownIcon className="w-5 h-5 text-gray-400" />
            )}
          </button>
          {expandedSections.thesis && (
            <div className="p-3 pt-0 border-t border-gray-100 space-y-2 max-h-64 overflow-y-auto">
              {filterOptions?.thesis.map((thesis) => (
                <label
                  key={thesis}
                  className="flex items-center text-sm hover:bg-gray-50 p-1 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={filters.thesis?.includes(thesis) || false}
                    onChange={() => handleThesisChange(thesis)}
                    className="mr-2 rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700">{thesis.replace(/_/g, " ")}</span>
                </label>
              ))}
            </div>
          )}
        </div>

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
            <div className="p-3 pt-0 border-t border-gray-100 space-y-2 max-h-64 overflow-y-auto">
              {filterOptions?.entities.slice(0, 30).map((entity) => (
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
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
