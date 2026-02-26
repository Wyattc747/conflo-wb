"use client";

import { useState } from "react";
import { Folder, FolderOpen, ChevronRight, ChevronDown, Plus } from "lucide-react";

interface FolderNode {
  id: string;
  name: string;
  is_system: boolean;
  parent_folder_id?: string | null;
}

interface FolderTreeProps {
  folders: FolderNode[];
  selectedFolderId?: string | null;
  onSelect: (folderId: string | null) => void;
  onCreateFolder?: () => void;
}

export function FolderTree({ folders, selectedFolderId, onSelect, onCreateFolder }: FolderTreeProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(folders.map((f) => f.id)));

  const rootFolders = folders.filter((f) => !f.parent_folder_id);
  const getChildren = (parentId: string) => folders.filter((f) => f.parent_folder_id === parentId);

  const toggleExpand = (folderId: string) => {
    const next = new Set(expanded);
    if (next.has(folderId)) next.delete(folderId);
    else next.add(folderId);
    setExpanded(next);
  };

  const renderFolder = (folder: FolderNode, depth: number = 0) => {
    const children = getChildren(folder.id);
    const isExpanded = expanded.has(folder.id);
    const isSelected = selectedFolderId === folder.id;

    return (
      <div key={folder.id}>
        <button
          onClick={() => onSelect(folder.id)}
          className={`w-full flex items-center gap-1.5 px-2 py-1.5 text-sm rounded hover:bg-gray-100 ${isSelected ? "bg-blue-50 text-[#2E75B6] font-medium" : "text-gray-700"}`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {children.length > 0 ? (
            <span onClick={(e) => { e.stopPropagation(); toggleExpand(folder.id); }} className="cursor-pointer">
              {isExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
            </span>
          ) : (
            <span className="w-3.5" />
          )}
          {isExpanded ? <FolderOpen className="h-4 w-4 text-[#2E75B6]" /> : <Folder className="h-4 w-4 text-gray-400" />}
          <span className="truncate">{folder.name}</span>
          {folder.is_system && <span className="text-[10px] text-gray-400 ml-auto">system</span>}
        </button>
        {isExpanded && children.map((child) => renderFolder(child, depth + 1))}
      </div>
    );
  };

  return (
    <div className="space-y-0.5">
      <button
        onClick={() => onSelect(null)}
        className={`w-full flex items-center gap-1.5 px-2 py-1.5 text-sm rounded hover:bg-gray-100 ${!selectedFolderId ? "bg-blue-50 text-[#2E75B6] font-medium" : "text-gray-700"}`}
      >
        <Folder className="h-4 w-4 text-gray-400" />
        <span>All Documents</span>
      </button>
      {rootFolders.map((f) => renderFolder(f))}
      {onCreateFolder && (
        <button
          onClick={onCreateFolder}
          className="w-full flex items-center gap-1.5 px-2 py-1.5 text-sm rounded hover:bg-gray-100 text-gray-500 mt-2"
        >
          <Plus className="h-4 w-4" />
          <span>New Folder</span>
        </button>
      )}
    </div>
  );
}
