"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, Wrench, MessageSquare } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { PunchListItem } from "@/types/punch-list";

const PRIORITY_STYLES: Record<string, string> = {
  CRITICAL: "text-red-600 font-semibold",
  HIGH: "text-orange-600 font-medium",
  MEDIUM: "text-gray-600",
  LOW: "text-gray-400",
};

const MOCK_PUNCH_ITEMS: PunchListItem[] = [
  {
    id: "1",
    project_id: "p1",
    number: 1,
    formatted_number: "PL-001",
    title: "Drywall damage at stairwell B, 2nd floor",
    description: "Drywall has visible damage and needs patching and repainting.",
    location: "Stairwell B, Level 2",
    category: "FINISHES",
    priority: "HIGH",
    status: "OPEN",
    assigned_to_sub_id: "sub1",
    assigned_to_sub_name: "Elite Drywall & Painting",
    assigned_to_user_name: "Tom Baker",
    due_date: "2026-03-05",
    before_photo_ids: ["ph1"],
    after_photo_ids: [],
    verification_photo_ids: [],
    comments_count: 2,
    created_by_name: "John Smith",
    created_at: "2026-02-20T10:00:00Z",
    updated_at: "2026-02-20T10:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    number: 2,
    formatted_number: "PL-002",
    title: "Missing fire caulk at MEP penetrations, Room 204",
    description: "Fire caulking missing at multiple MEP penetrations through rated wall.",
    location: "Room 204, Level 2",
    category: "FIRE_PROTECTION",
    priority: "CRITICAL",
    status: "IN_PROGRESS",
    assigned_to_sub_id: "sub2",
    assigned_to_sub_name: "Summit Fire Protection",
    assigned_to_user_name: "Ray Martinez",
    due_date: "2026-02-28",
    before_photo_ids: ["ph2", "ph3"],
    after_photo_ids: [],
    verification_photo_ids: [],
    comments_count: 3,
    created_by_name: "Sarah Johnson",
    created_at: "2026-02-18T14:00:00Z",
    updated_at: "2026-02-22T09:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    number: 3,
    formatted_number: "PL-003",
    title: "HVAC diffuser misaligned in conference room",
    description: "Supply air diffuser in main conference room is not centered in ceiling tile.",
    location: "Conference Room 101, Level 1",
    category: "MECHANICAL",
    priority: "MEDIUM",
    status: "COMPLETED_BY_SUB",
    assigned_to_sub_id: "sub3",
    assigned_to_sub_name: "Summit Mechanical",
    assigned_to_user_name: "Jake Wilson",
    due_date: "2026-03-01",
    before_photo_ids: ["ph4"],
    after_photo_ids: ["ph5"],
    verification_photo_ids: [],
    completion_notes: "Diffuser repositioned and centered. Ceiling tile replaced.",
    completed_by: "sub_u1",
    completed_at: "2026-02-24T16:00:00Z",
    comments_count: 1,
    created_by_name: "Mike Chen",
    created_at: "2026-02-15T11:00:00Z",
    updated_at: "2026-02-24T16:00:00Z",
  },
  {
    id: "4",
    project_id: "p1",
    number: 4,
    formatted_number: "PL-004",
    title: "Scratched door hardware, main entrance",
    description: "Lever handle on main entrance door has visible scratches from construction activity.",
    location: "Main Entrance, Level 1",
    category: "DOORS_HARDWARE",
    priority: "LOW",
    status: "VERIFIED_BY_GC",
    assigned_to_sub_id: "sub4",
    assigned_to_sub_name: "Premier Door & Hardware",
    assigned_to_user_name: "Dan Lee",
    due_date: "2026-03-10",
    before_photo_ids: ["ph6"],
    after_photo_ids: ["ph7"],
    verification_photo_ids: ["ph8"],
    completion_notes: "Hardware replaced with new unit.",
    completed_by: "sub_u2",
    completed_at: "2026-02-22T10:00:00Z",
    verification_notes: "Verified -- new hardware installed correctly. Closing item.",
    verified_by: "u1",
    verified_at: "2026-02-23T14:00:00Z",
    comments_count: 0,
    created_by_name: "John Smith",
    created_at: "2026-02-12T09:00:00Z",
    updated_at: "2026-02-23T14:00:00Z",
  },
];

export default function PunchListPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [sortKey, setSortKey] = useState("number");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_PUNCH_ITEMS;
  if (statusFilter) filtered = filtered.filter((p) => p.status === statusFilter);
  if (priorityFilter) filtered = filtered.filter((p) => p.priority === priorityFilter);
  if (categoryFilter) filtered = filtered.filter((p) => p.category === categoryFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (p) =>
        p.title.toLowerCase().includes(s) ||
        p.formatted_number.toLowerCase().includes(s) ||
        (p.location && p.location.toLowerCase().includes(s))
    );
  }

  const columns: Column<PunchListItem>[] = [
    {
      key: "number",
      label: "#",
      sortable: true,
      className: "w-24",
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
      key: "location",
      label: "Location",
      render: (row) => (
        <span className="text-sm text-gray-600">{row.location || "—"}</span>
      ),
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
      key: "assigned_to_sub_name",
      label: "Assigned To",
      render: (row) => row.assigned_to_sub_name || "Unassigned",
    },
    {
      key: "priority",
      label: "Priority",
      sortable: true,
      render: (row) => (
        <span className={`text-sm ${PRIORITY_STYLES[row.priority] || ""}`}>
          {row.priority}
        </span>
      ),
    },
    {
      key: "due_date",
      label: "Due Date",
      sortable: true,
      render: (row) => {
        if (!row.due_date) return "—";
        const due = new Date(row.due_date + "T00:00:00");
        const isOverdue = ["OPEN", "IN_PROGRESS"].includes(row.status) && due < new Date();
        return (
          <span className={isOverdue ? "text-red-600 font-medium" : ""}>
            {due.toLocaleDateString()}
          </span>
        );
      },
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

  const hasData = MOCK_PUNCH_ITEMS.length > 0;

  return (
    <div>
      <PageHeader
        title="Punch List"
        subtitle="Track and resolve punch list items"
        action={
          <button
            onClick={() => router.push(`/app/projects/${projectId}/punch-list/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2 w-full sm:w-auto justify-center"
          >
            <Plus className="h-4 w-4" />
            New Punch Item
          </button>
        }
      />

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search punch list..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[
              {
                key: "status",
                label: "All Statuses",
                value: statusFilter,
                onChange: setStatusFilter,
                options: [
                  { label: "Open", value: "OPEN" },
                  { label: "In Progress", value: "IN_PROGRESS" },
                  { label: "Completed by Sub", value: "COMPLETED_BY_SUB" },
                  { label: "Verified by GC", value: "VERIFIED_BY_GC" },
                  { label: "Closed", value: "CLOSED" },
                ],
              },
              {
                key: "priority",
                label: "All Priorities",
                value: priorityFilter,
                onChange: setPriorityFilter,
                options: [
                  { label: "Critical", value: "CRITICAL" },
                  { label: "High", value: "HIGH" },
                  { label: "Medium", value: "MEDIUM" },
                  { label: "Low", value: "LOW" },
                ],
              },
              {
                key: "category",
                label: "All Categories",
                value: categoryFilter,
                onChange: setCategoryFilter,
                options: [
                  { label: "Finishes", value: "FINISHES" },
                  { label: "Fire Protection", value: "FIRE_PROTECTION" },
                  { label: "Mechanical", value: "MECHANICAL" },
                  { label: "Electrical", value: "ELECTRICAL" },
                  { label: "Plumbing", value: "PLUMBING" },
                  { label: "Doors/Hardware", value: "DOORS_HARDWARE" },
                  { label: "Other", value: "OTHER" },
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
            onRowClick={(row) => router.push(`/app/projects/${projectId}/punch-list/${row.id}`)}
            page={page}
            totalPages={1}
            total={filtered.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={Wrench}
          title="No punch list items yet"
          description="Create your first punch item to start tracking deficiencies."
          actionLabel="Create Punch Item"
          onAction={() => router.push(`/app/projects/${projectId}/punch-list/new`)}
        />
      )}
    </div>
  );
}
