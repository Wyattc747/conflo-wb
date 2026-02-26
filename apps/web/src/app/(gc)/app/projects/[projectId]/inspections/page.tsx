"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, ClipboardCheck, MessageSquare } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { Inspection } from "@/types/inspection";

const RESULT_STYLES: Record<string, string> = {
  PASS: "bg-green-100 text-green-700",
  FAIL: "bg-red-100 text-red-700",
  PARTIAL: "bg-yellow-100 text-yellow-700",
};

const MOCK_INSPECTIONS: Inspection[] = [
  {
    id: "1",
    project_id: "p1",
    number: 1,
    formatted_number: "INSP-001",
    title: "Foundation footing inspection",
    template_id: "t1",
    template_name: "Concrete Pre-Pour",
    category: "STRUCTURAL",
    scheduled_date: "2026-02-26",
    scheduled_time: "09:00",
    location: "Grid A-C, Level 0",
    inspector_name: "David Brooks",
    inspector_company: "City Building Dept",
    status: "COMPLETED",
    overall_result: "PASS",
    checklist_results: [
      { item_label: "Rebar placement verified", result: "PASS", notes: null },
      { item_label: "Form dimensions verified", result: "PASS", notes: null },
      { item_label: "Soil bearing confirmed", result: "PASS", notes: "Bearing at 5000 PSF per geotech" },
    ],
    photo_ids: ["ph1", "ph2"],
    notes: "All items pass. Cleared for concrete pour.",
    comments_count: 1,
    created_by_name: "John Smith",
    created_at: "2026-02-20T10:00:00Z",
    completed_at: "2026-02-26T11:30:00Z",
    updated_at: "2026-02-26T11:30:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    number: 2,
    formatted_number: "INSP-002",
    title: "Electrical rough-in inspection - Level 2",
    template_id: "t2",
    template_name: "Electrical Rough-In",
    category: "ELECTRICAL",
    scheduled_date: "2026-03-01",
    scheduled_time: "10:00",
    location: "Level 2, All Areas",
    inspector_name: "Karen White",
    inspector_company: "City Building Dept",
    status: "SCHEDULED",
    overall_result: null,
    checklist_results: [],
    photo_ids: [],
    notes: null,
    comments_count: 0,
    created_by_name: "Mike Chen",
    created_at: "2026-02-22T09:00:00Z",
    completed_at: null,
    updated_at: "2026-02-22T09:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    number: 3,
    formatted_number: "INSP-003",
    title: "Fire stopping inspection - Room 204",
    template_id: "t3",
    template_name: "Fire Protection",
    category: "FIRE_PROTECTION",
    scheduled_date: "2026-03-03",
    scheduled_time: "14:00",
    location: "Room 204, Level 2",
    inspector_name: "David Brooks",
    inspector_company: "Fire Marshal Office",
    status: "SCHEDULED",
    overall_result: null,
    checklist_results: [],
    photo_ids: [],
    notes: "Inspection tied to PL-002 completion. Confirm fire caulk work is done before date.",
    comments_count: 2,
    created_by_name: "Sarah Johnson",
    created_at: "2026-02-24T08:00:00Z",
    completed_at: null,
    updated_at: "2026-02-24T08:00:00Z",
  },
  {
    id: "4",
    project_id: "p1",
    number: 4,
    formatted_number: "INSP-004",
    title: "Roofing membrane inspection",
    template_id: "t4",
    template_name: "Roofing",
    category: "BUILDING_ENVELOPE",
    scheduled_date: "2026-02-25",
    scheduled_time: "08:00",
    location: "Roof, All Areas",
    inspector_name: "Mark Taylor",
    inspector_company: "ABC General Contractors",
    status: "COMPLETED",
    overall_result: "FAIL",
    checklist_results: [
      { item_label: "Membrane adhesion test", result: "PASS", notes: null },
      { item_label: "Seam integrity", result: "FAIL", notes: "Seam separation at parapet NE corner" },
      { item_label: "Flashing details", result: "PASS", notes: null },
      { item_label: "Drainage slope verification", result: "PASS", notes: null },
    ],
    photo_ids: ["ph3"],
    notes: "Failed due to seam separation at NE parapet. Sub to repair and re-inspect.",
    comments_count: 3,
    created_by_name: "Mike Chen",
    created_at: "2026-02-18T07:00:00Z",
    completed_at: "2026-02-25T10:00:00Z",
    updated_at: "2026-02-25T10:00:00Z",
  },
];

export default function InspectionsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState("number");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_INSPECTIONS;
  if (statusFilter) filtered = filtered.filter((i) => i.status === statusFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (i) =>
        i.title.toLowerCase().includes(s) ||
        i.formatted_number.toLowerCase().includes(s) ||
        (i.inspector_name && i.inspector_name.toLowerCase().includes(s))
    );
  }

  const columns: Column<Inspection>[] = [
    {
      key: "number",
      label: "#",
      sortable: true,
      className: "w-28",
      render: (row) => (
        <span className="font-mono text-sm font-medium text-[#1B2A4A]">{row.formatted_number}</span>
      ),
    },
    {
      key: "title",
      label: "Title",
      sortable: true,
      className: "max-w-xs",
      render: (row) => <span className="font-medium truncate block max-w-xs">{row.title}</span>,
    },
    {
      key: "category",
      label: "Category",
      sortable: true,
      render: (row) => (
        <span className="text-sm text-gray-600">{row.category.replace(/_/g, " ")}</span>
      ),
    },
    {
      key: "scheduled_date",
      label: "Scheduled Date",
      sortable: true,
      render: (row) => {
        if (!row.scheduled_date) return "—";
        const date = new Date(row.scheduled_date + "T00:00:00");
        return (
          <span>
            {date.toLocaleDateString()}
            {row.scheduled_time && <span className="text-gray-400 ml-1">{row.scheduled_time}</span>}
          </span>
        );
      },
    },
    {
      key: "inspector_name",
      label: "Inspector",
      render: (row) => (
        <div>
          <span className="block">{row.inspector_name || "—"}</span>
          {row.inspector_company && (
            <span className="text-xs text-gray-400">{row.inspector_company}</span>
          )}
        </div>
      ),
    },
    {
      key: "overall_result",
      label: "Result",
      render: (row) =>
        row.overall_result ? (
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${RESULT_STYLES[row.overall_result] || "bg-gray-100 text-gray-600"}`}>
            {row.overall_result}
          </span>
        ) : (
          <span className="text-sm text-gray-400">--</span>
        ),
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: "comments_count",
      label: "",
      className: "w-12",
      render: (row) =>
        row.comments_count > 0 ? (
          <span className="flex items-center gap-1 text-xs text-gray-400">
            <MessageSquare className="h-3.5 w-3.5" />
            {row.comments_count}
          </span>
        ) : null,
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

  const hasData = MOCK_INSPECTIONS.length > 0;

  return (
    <div>
      <PageHeader
        title="Inspections"
        subtitle="Schedule and conduct project inspections"
        action={
          <button
            onClick={() => router.push(`/app/projects/${projectId}/inspections/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Inspection
          </button>
        }
      />

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search inspections..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[
              {
                key: "status",
                label: "All Statuses",
                value: statusFilter,
                onChange: setStatusFilter,
                options: [
                  { label: "Scheduled", value: "SCHEDULED" },
                  { label: "In Progress", value: "IN_PROGRESS" },
                  { label: "Completed", value: "COMPLETED" },
                  { label: "Failed", value: "FAILED" },
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
            onRowClick={(row) => router.push(`/app/projects/${projectId}/inspections/${row.id}`)}
            page={page}
            totalPages={1}
            total={filtered.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={ClipboardCheck}
          title="No inspections yet"
          description="Schedule your first inspection to ensure quality standards."
          actionLabel="Schedule Inspection"
          onAction={() => router.push(`/app/projects/${projectId}/inspections/new`)}
        />
      )}
    </div>
  );
}
