"use client";

import { useState } from "react";

interface KanbanColumn<T> {
  id: string;
  title: string;
  color: string;
  items: T[];
}

interface KanbanBoardProps<T> {
  columns: KanbanColumn<T>[];
  renderCard: (item: T) => React.ReactNode;
  onDrop?: (itemId: string, targetColumn: string) => void;
  getItemId: (item: T) => string;
}

export function KanbanBoard<T>({ columns, renderCard, onDrop, getItemId }: KanbanBoardProps<T>) {
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);

  const handleDragStart = (e: React.DragEvent, item: T) => {
    e.dataTransfer.setData("text/plain", getItemId(item));
  };

  const handleDragOver = (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    setDragOverColumn(columnId);
  };

  const handleDragLeave = () => {
    setDragOverColumn(null);
  };

  const handleDrop = (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    setDragOverColumn(null);
    const itemId = e.dataTransfer.getData("text/plain");
    onDrop?.(itemId, columnId);
  };

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {columns.map((col) => (
        <div
          key={col.id}
          className={`flex-1 min-w-[280px] rounded-lg border ${dragOverColumn === col.id ? "border-[#2E75B6] bg-blue-50/50" : "border-gray-200 bg-gray-50/50"}`}
          onDragOver={(e) => handleDragOver(e, col.id)}
          onDragLeave={handleDragLeave}
          onDrop={(e) => handleDrop(e, col.id)}
        >
          <div className="p-3 border-b">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${col.color}`} />
              <span className="text-sm font-medium text-gray-700">{col.title}</span>
              <span className="text-xs text-gray-400 ml-auto">{col.items.length}</span>
            </div>
          </div>
          <div className="p-2 space-y-2 min-h-[200px]">
            {col.items.map((item) => (
              <div
                key={getItemId(item)}
                draggable
                onDragStart={(e) => handleDragStart(e, item)}
                className="cursor-grab active:cursor-grabbing"
              >
                {renderCard(item)}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
