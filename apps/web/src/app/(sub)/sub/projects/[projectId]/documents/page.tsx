"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { FolderOpen, FileText, Tag } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { FolderTree } from "@/components/shared/FolderTree";
import type { Document, DocumentFolder } from "@/types/document";

const MOCK_FOLDERS: DocumentFolder[] = [
  { id: "f1", project_id: "p1", name: "Contracts", parent_folder_id: null, is_system: true, created_at: "2026-02-01T00:00:00Z" },
  { id: "f2", project_id: "p1", name: "Specifications", parent_folder_id: null, is_system: true, created_at: "2026-02-01T00:00:00Z" },
  { id: "f3", project_id: "p1", name: "Permits", parent_folder_id: null, is_system: false, created_at: "2026-02-05T00:00:00Z" },
];

const MOCK_DOCUMENTS: Document[] = [
  {
    id: "1",
    project_id: "p1",
    title: "Subcontract Agreement",
    description: "Executed subcontract agreement for steel scope.",
    category: "CONTRACT",
    folder_id: "f1",
    folder_name: "Contracts",
    file_id: "file1",
    tags: ["contract"],
    version: 1,
    uploaded_by_name: "John Smith",
    created_at: "2026-02-05T10:00:00Z",
    updated_at: "2026-02-05T10:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    title: "Division 05 - Metals Specification",
    description: "Structural steel specifications.",
    category: "SPECIFICATION",
    folder_id: "f2",
    folder_name: "Specifications",
    file_id: "file2",
    tags: ["spec", "structural"],
    version: 1,
    uploaded_by_name: "Sarah Johnson",
    created_at: "2026-02-08T09:00:00Z",
    updated_at: "2026-02-08T09:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    title: "Building Permit",
    category: "PERMIT",
    folder_id: "f3",
    folder_name: "Permits",
    file_id: "file3",
    tags: ["permit"],
    version: 1,
    uploaded_by_name: "John Smith",
    created_at: "2026-02-10T11:00:00Z",
    updated_at: "2026-02-10T11:00:00Z",
  },
];

const CATEGORY_STYLES: Record<string, string> = {
  CONTRACT: "bg-purple-100 text-purple-700",
  SPECIFICATION: "bg-blue-100 text-blue-700",
  PERMIT: "bg-green-100 text-green-700",
  REPORT: "bg-gray-100 text-gray-600",
};

export default function SubDocumentsPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState("title");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_DOCUMENTS;
  if (selectedFolderId) filtered = filtered.filter((d) => d.folder_id === selectedFolderId);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (d) =>
        d.title.toLowerCase().includes(s) ||
        (d.description && d.description.toLowerCase().includes(s))
    );
  }

  const columns: Column<Document>[] = [
    {
      key: "title",
      label: "Title",
      sortable: true,
      className: "max-w-sm",
      render: (row) => (
        <div className="flex items-start gap-2">
          <FileText className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <span className="font-medium truncate block max-w-sm">{row.title}</span>
            {row.description && (
              <span className="text-xs text-gray-500 truncate block max-w-sm">{row.description}</span>
            )}
          </div>
        </div>
      ),
    },
    {
      key: "category",
      label: "Category",
      render: (row) =>
        row.category ? (
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${CATEGORY_STYLES[row.category] || "bg-gray-100 text-gray-600"}`}>
            {row.category}
          </span>
        ) : "\u2014",
    },
    {
      key: "folder_name",
      label: "Folder",
      render: (row) => row.folder_name || "Unfiled",
    },
    {
      key: "version",
      label: "Version",
      render: (row) => <span className="text-sm text-gray-600">v{row.version}</span>,
    },
    {
      key: "updated_at",
      label: "Updated",
      sortable: true,
      render: (row) => new Date(row.updated_at).toLocaleDateString(),
    },
  ];

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortOrder("asc");
    }
  };

  const hasData = MOCK_DOCUMENTS.length > 0;

  return (
    <div>
      <PageHeader title="Documents" subtitle="View and download project documents" />

      {hasData ? (
        <div className="flex gap-6">
          <div className="w-56 flex-shrink-0">
            <div className="bg-white rounded-lg border border-gray-200 p-3">
              <FolderTree
                folders={MOCK_FOLDERS}
                selectedFolderId={selectedFolderId}
                onSelect={setSelectedFolderId}
              />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <FilterBar
              searchPlaceholder="Search documents..."
              searchValue={search}
              onSearchChange={setSearch}
              filters={[]}
            />
            <DataTable
              columns={columns}
              data={filtered}
              sortKey={sortKey}
              sortOrder={sortOrder}
              onSort={handleSort}
              page={page}
              totalPages={1}
              total={filtered.length}
              onPageChange={setPage}
            />
          </div>
        </div>
      ) : (
        <EmptyState
          icon={FolderOpen}
          title="No documents yet"
          description="Documents shared by the GC will appear here."
        />
      )}
    </div>
  );
}
