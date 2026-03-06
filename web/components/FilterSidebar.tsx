"use client";

import { ChatFilters, FilterOptions } from "@/lib/types";

interface FilterSidebarProps {
  filters: ChatFilters;
  filterOptions: FilterOptions | null;
  onFiltersChange: (filters: ChatFilters) => void;
  onClear: () => void;
}

export default function FilterSidebar({
  filters,
  filterOptions,
  onFiltersChange,
  onClear,
}: FilterSidebarProps) {
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

  return (
    <div className="w-64 border-r border-gray-200 p-4 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Filters</h2>
        <button
          onClick={onClear}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Clear
        </button>
      </div>

      {/* Thesis */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Thesis
        </label>
        <select
          value={filters.thesis || ""}
          onChange={(e) =>
            onFiltersChange({ ...filters, thesis: e.target.value || null })
          }
          className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
        >
          <option value="">All</option>
          {filterOptions?.thesis.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {/* Sector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Sector
        </label>
        <div className="space-y-1">
          {filterOptions?.sector.map((sector) => (
            <label key={sector} className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={filters.sector?.includes(sector) || false}
                onChange={() => handleSectorChange(sector)}
                className="mr-2"
              />
              {sector}
            </label>
          ))}
        </div>
      </div>

      {/* Entities (top 10) */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Entities
        </label>
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {filterOptions?.entities.slice(0, 20).map((entity) => (
            <label key={entity} className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={filters.entities?.includes(entity) || false}
                onChange={() => handleEntityChange(entity)}
                className="mr-2"
              />
              {entity}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
