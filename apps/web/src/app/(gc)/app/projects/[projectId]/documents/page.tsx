"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, FolderOpen, FileText, Tag } from "lucide-react";
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
  { id: "f4", project_id: "p1", name: "Insurance", parent_folder_id: "f1", is_system: false, created_at: "2026-02-05T00:00:00Z" },
];

const MOCK_DOCUMENTS: Document[] = [
  {
    id: "1",
    project_id: "p1",
    title: "Owner-GC Contract Agreement",
    description: "Prime contract agreement between owner and general contractor.",
    category: "CONTRACT",
    folder_id: "f1",
    folder_name: "Contracts",
    file_id: "file1",
    tags: ["contract", "legal"],
    version: 2,
    uploaded_by_name: "John Smith",
    created_at: "2026-02-05T10:00:00Z",
    updated_at: "2026-02-15T14:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    title: "Division 05 - Metals Specification",
    description: "Structural steel specifications for the project.",
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
    title: "Building Permit - Main Structure",
    description: "City-issued building permit for main structure construction.",
    category: "PERMIT",
    folder_id: "f3",
    folder_name: "Permits",
    file_id: "file3",
    tags: ["permit", "city"],
    version: 1,
    uploaded_by_name: "John Smith",
    created_at: "2026-02-10T11:00:00Z",
    updated_at: "2026-02-10T11:00:00Z",
  },
  {
    id: "4",
    project_id: "p1",
    title: "Subcontractor COI - Apex Steel",
    description: "Certificate of insurance for Apex Steel Fabricators.",
    category: "INSURANCE",
    folder_id: "f4",
    folder_name: "Insurance",
    file_id: "file4",
    tags: ["insurance", "coi"],
    version: 1,
    uploaded_by_name: "Jane Doe",
    created_at: "2026-02-12T16:00:00Z",
    updated_at: "2026-02-12T16:00:00Z",
  },
  {
    id: "5",
    project_id: "p1",
    title: "Geotechnical Report",
    description: "Site soils and geotechnical investigation report.",
    category: "REPORT",
    folder_id: null,
    folder_name: null,
    file_id: "file5",
    tags: ["geotech", "soils"],
    version: 1,
    uploaded_by_name: "Mike Chen",
    created_at: "2026-02-03T08:00:00Z",
    updated_at: "2026-02-03T08:00:00Z",
  },
];

const CATEGORY_STYLES: Record<string, string> = {
  CONTRACT: "bg-purple-100 text-purple-700",
  SPECIFICATION: "bg-blue-100 text-blue-700",
  PERMIT: "bg-green-100 text-green-700",
  INSURANCE: "bg-yellow-100 text-yellow-700",
  REPORT: "bg-gray-100 text-gray-600",
};

export default function DocumentsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState("title");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_DOCUMENTS;
  if (selectedFolderId) filtered = filtered.filter((d) => d.folder_id === selectedFolderId);
  if (categoryFilter) filtered = filtered.filter((d) => d.category === categoryFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (d) =>
        d.title.toLowerCase().includes(s) ||
        (d.description && d.description.toLowerCase().includes(s)) ||
        d.tags.some((t) => t.toLowerCase().includes(s))
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
      sortable: true,
      render: (row) =>
        row.category ? (
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${CATEGORY_STYLES[row.category] || "bg-gray-100 text-gray-600"}`}>
            {row.category}
          </span>
        ) : (
          "\u2014"
        ),
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
      key: "tags",
      label: "Tags",
      render: (row) =>
        row.tags.length > 0 ? (
          <div className="flex items-center gap-1">
            {row.tags.slice(0, 2).map((tag) => (
              <span key={tag} className="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-[10px]">
                <Tag className="h-2.5 w-2.5" />{tag}
              </span>
            ))}
            {row.tags.length > 2 && (
              <span className="text-[10px] text-gray-400">+{row.tags.length - 2}</span>
            )}
          </div>
        ) : null,
    },
    {
      key: "uploaded_by_name",
      label: "Uploaded By",
      render: (row) => row.uploaded_by_name || "\u2014",
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
      setSortOrder("desc");
    }
  };

  const hasData = MOCK_DOCUMENTS.length > 0;

  return (
    <div>
      <PageHeader
        title="Documents"
        subtitle="Upload and organize project documents"
        action={
          <button
            onClick={() => router.push(`/app/projects/${projectId}/documents/upload`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Upload Document
          </button>
        }
      />

      {hasData ? (
        <div className="flex gap-6">
          <div className="w-56 flex-shrink-0">
            <div className="bg-white rounded-lg border border-gray-200 p-3">
              <FolderTree
                folders={MOCK_FOLDERS}
                selectedFolderId={selectedFolderId}
                onSelect={setSelectedFolderId}
                onCreateFolder={() => console.log("create folder")}
              />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <FilterBar
              searchPlaceholder="Search documents..."
              searchValue={search}
              onSearchChange={setSearch}
              filters={[
                {
                  key: "category",
                  label: "All Categories",
                  value: categoryFilter,
                  onChange: setCategoryFilter,
                  options: [
                    { label: "Contract", value: "CONTRACT" },
                    { label: "Specification", value: "SPECIFICATION" },
                    { label: "Permit", value: "PERMIT" },
                    { label: "Insurance", value: "INSURANCE" },
                    { label: "Report", value: "REPORT" },
                  ],
                },
              ]}
            />
            <DataTable
              columns={columns}
              data={filtered}
              sortKey={sortKey}
              sortOrder={sortOrder}
              onSort={handleSort}
              onRowClick={(row) => router.push(`/app/projects/${projectId}/documents/${row.id}`)}
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
          description="Upload your first document to start organizing project files."
          actionLabel="Upload Document"
          onAction={() => router.push(`/app/projects/${projectId}/documents/upload`)}
        />
      )}
    </div>
  );
}
