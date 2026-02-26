"use client";

import { LayoutGrid, List } from "lucide-react";

interface ViewToggleProps {
  view: "table" | "board";
  onViewChange: (view: "table" | "board") => void;
}

export function ViewToggle({ view, onViewChange }: ViewToggleProps) {
  return (
    <div className="flex items-center border rounded-lg overflow-hidden">
      <button
        onClick={() => onViewChange("table")}
        className={`p-2 ${view === "table" ? "bg-[#1B2A4A] text-white" : "bg-white text-gray-500 hover:bg-gray-50"}`}
        title="Table view"
      >
        <List className="h-4 w-4" />
      </button>
      <button
        onClick={() => onViewChange("board")}
        className={`p-2 ${view === "board" ? "bg-[#1B2A4A] text-white" : "bg-white text-gray-500 hover:bg-gray-50"}`}
        title="Board view"
      >
        <LayoutGrid className="h-4 w-4" />
      </button>
    </div>
  );
}
