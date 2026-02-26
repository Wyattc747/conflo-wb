"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { PenTool, Layers, Check, Download } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import type { DrawingSet } from "@/types/drawing";

const DISCIPLINE_STYLES: Record<string, string> = {
  ARCHITECTURAL: "bg-blue-100 text-blue-700",
  STRUCTURAL: "bg-purple-100 text-purple-700",
  MECHANICAL: "bg-orange-100 text-orange-700",
  ELECTRICAL: "bg-yellow-100 text-yellow-700",
  PLUMBING: "bg-cyan-100 text-cyan-700",
};

const MOCK_DRAWING_SETS: DrawingSet[] = [
  {
    id: "1",
    project_id: "p1",
    set_number: "A",
    title: "Architectural Set - 100% CD",
    discipline: "ARCHITECTURAL",
    received_from: "HKS Architects",
    is_current_set: true,
    sheet_count: 42,
    sheets: [],
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-02-20T10:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    set_number: "S",
    title: "Structural Set - 100% CD",
    discipline: "STRUCTURAL",
    received_from: "Thornton Tomasetti",
    is_current_set: true,
    sheet_count: 28,
    sheets: [],
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-02-18T14:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    set_number: "E",
    title: "Electrical Set - 100% CD",
    discipline: "ELECTRICAL",
    received_from: "Arup",
    is_current_set: true,
    sheet_count: 22,
    sheets: [],
    created_at: "2026-02-03T11:00:00Z",
    updated_at: "2026-02-15T10:00:00Z",
  },
];

export default function SubDrawingsPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [disciplineFilter, setDisciplineFilter] = useState("");
  const [sortKey, setSortKey] = useState("set_number");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_DRAWING_SETS;
  if (disciplineFilter) filtered = filtered.filter((d) => d.discipline === disciplineFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (d) =>
        d.title.toLowerCase().includes(s) ||
        d.set_number.toLowerCase().includes(s)
    );
  }

  const columns: Column<DrawingSet>[] = [
    {
      key: "set_number",
      label: "Set",
      sortable: true,
      className: "w-20",
      render: (row) => (
        <span className="font-mono text-sm font-medium text-[#1B2A4A]">{row.set_number}</span>
      ),
    },
    {
      key: "title",
      label: "Title",
      sortable: true,
      className: "max-w-sm",
      render: (row) => <span className="font-medium truncate block max-w-sm">{row.title}</span>,
    },
    {
      key: "discipline",
      label: "Discipline",
      render: (row) =>
        row.discipline ? (
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${DISCIPLINE_STYLES[row.discipline] || "bg-gray-100 text-gray-600"}`}>
            {row.discipline}
          </span>
        ) : "\u2014",
    },
    {
      key: "received_from",
      label: "Received From",
      render: (row) => row.received_from || "\u2014",
    },
    {
      key: "sheet_count",
      label: "Sheets",
      render: (row) => (
        <span className="flex items-center gap-1 text-sm">
          <Layers className="h-3.5 w-3.5 text-gray-400" />
          {row.sheet_count}
        </span>
      ),
    },
    {
      key: "is_current_set",
      label: "Current",
      render: (row) =>
        row.is_current_set ? (
          <span className="flex items-center gap-1 text-green-600 text-sm">
            <Check className="h-4 w-4" />Current
          </span>
        ) : (
          <span className="text-sm text-gray-400">Superseded</span>
        ),
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

  const hasData = MOCK_DRAWING_SETS.length > 0;

  return (
    <div>
      <PageHeader title="Drawings" subtitle="View and download project drawings" />

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search drawings..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[
              {
                key: "discipline",
                label: "All Disciplines",
                value: disciplineFilter,
                onChange: setDisciplineFilter,
                options: [
                  { label: "Architectural", value: "ARCHITECTURAL" },
                  { label: "Structural", value: "STRUCTURAL" },
                  { label: "Mechanical", value: "MECHANICAL" },
                  { label: "Electrical", value: "ELECTRICAL" },
                  { label: "Plumbing", value: "PLUMBING" },
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
            page={page}
            totalPages={1}
            total={filtered.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={PenTool}
          title="No drawings yet"
          description="Drawings will appear here when uploaded by the GC."
        />
      )}
    </div>
  );
}
