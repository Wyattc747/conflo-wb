"use client";

import { Search, X } from "lucide-react";
import { useState } from "react";

interface FilterOption {
  label: string;
  value: string;
}

interface FilterBarProps {
  searchPlaceholder?: string;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  filters?: {
    key: string;
    label: string;
    options: FilterOption[];
    value?: string;
    onChange?: (value: string) => void;
  }[];
}

export function FilterBar({
  searchPlaceholder = "Search...",
  searchValue = "",
  onSearchChange,
  filters = [],
}: FilterBarProps) {
  const [localSearch, setLocalSearch] = useState(searchValue);

  const handleSearchSubmit = () => {
    onSearchChange?.(localSearch);
  };

  return (
    <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
      {/* Search */}
      <div className="relative w-full sm:flex-1 sm:min-w-[200px] sm:max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder={searchPlaceholder}
          value={localSearch}
          onChange={(e) => setLocalSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearchSubmit()}
          className="w-full pl-9 pr-8 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20 focus:border-[#1B2A4A]"
        />
        {localSearch && (
          <button
            onClick={() => { setLocalSearch(""); onSearchChange?.(""); }}
            className="absolute right-2 top-1/2 -translate-y-1/2"
          >
            <X className="h-4 w-4 text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      {/* Filter dropdowns */}
      {filters.map((filter) => (
        <select
          key={filter.key}
          value={filter.value || ""}
          onChange={(e) => filter.onChange?.(e.target.value)}
          className="flex-1 sm:flex-none px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20 focus:border-[#1B2A4A]"
        >
          <option value="">{filter.label}</option>
          {filter.options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ))}
    </div>
  );
}
