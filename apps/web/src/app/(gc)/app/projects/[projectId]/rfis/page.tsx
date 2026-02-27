"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, HelpCircle, MessageSquare, AlertCircle } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { RFI } from "@/types/rfi";

const PRIORITY_STYLES: Record<string, string> = {
  URGENT: "text-red-600 font-semibold",
  HIGH: "text-orange-600 font-medium",
  NORMAL: "text-gray-600",
  LOW: "text-gray-400",
};

// Mock data for UI development
const MOCK_RFIS: RFI[] = [
  {
    id: "1",
    project_id: "p1",
    number: 1,
    formatted_number: "RFI-001",
    subject: "Concrete mix design for foundation footings",
    question: "What concrete mix design should be used for the spread footings on grid A-C?",
    status: "OPEN",
    priority: "HIGH",
    assigned_to: "u2",
    assigned_to_name: "Sarah Johnson",
    due_date: "2026-03-01",
    days_open: 5,
    cost_impact: false,
    schedule_impact: true,
    created_by_name: "John Smith",
    created_at: "2026-02-20T10:00:00Z",
    updated_at: "2026-02-20T10:00:00Z",
    comments_count: 3,
  },
  {
    id: "2",
    project_id: "p1",
    number: 2,
    formatted_number: "RFI-002",
    subject: "Steel connection detail at grid line 4",
    question: "The structural drawings show a moment connection at grid 4/B but the specs call for a shear connection. Please clarify.",
    official_response: "Use moment connection per drawing S-201. Spec will be updated in next revision.",
    status: "RESPONDED",
    priority: "URGENT",
    assigned_to: "u3",
    assigned_to_name: "Mike Chen",
    due_date: "2026-02-22",
    days_open: null,
    cost_impact: true,
    schedule_impact: true,
    responded_by_name: "Mike Chen",
    responded_at: "2026-02-22T14:00:00Z",
    created_by_name: "John Smith",
    created_at: "2026-02-18T09:00:00Z",
    updated_at: "2026-02-22T14:00:00Z",
    comments_count: 5,
  },
  {
    id: "3",
    project_id: "p1",
    number: 3,
    formatted_number: "RFI-003",
    subject: "Exterior paint color for south elevation",
    question: "Owner has requested a color change on the south elevation. Please confirm new color selection.",
    status: "CLOSED",
    priority: "NORMAL",
    assigned_to: "u2",
    assigned_to_name: "Sarah Johnson",
    cost_impact: false,
    schedule_impact: false,
    created_by_name: "Jane Doe",
    created_at: "2026-02-10T11:00:00Z",
    updated_at: "2026-02-15T16:00:00Z",
    comments_count: 1,
  },
];

export default function RFIsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [sortKey, setSortKey] = useState("number");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_RFIS;
  if (statusFilter) filtered = filtered.filter((r) => r.status === statusFilter);
  if (priorityFilter) filtered = filtered.filter((r) => r.priority === priorityFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (r) => r.subject.toLowerCase().includes(s) || r.formatted_number.toLowerCase().includes(s)
    );
  }

  const columns: Column<RFI>[] = [
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
      key: "subject",
      label: "Subject",
      sortable: true,
      className: "max-w-xs",
      render: (row) => (
        <div>
          <span className="font-medium truncate block max-w-xs">{row.subject}</span>
          <div className="flex items-center gap-2 mt-0.5">
            {row.cost_impact && (
              <span className="text-[10px] text-red-600 flex items-center gap-0.5">
                <AlertCircle className="h-3 w-3" />$
              </span>
            )}
            {row.schedule_impact && (
              <span className="text-[10px] text-orange-600 flex items-center gap-0.5">
                <AlertCircle className="h-3 w-3" />Schedule
              </span>
            )}
          </div>
        </div>
      ),
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
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
      key: "assigned_to_name",
      label: "Assigned To",
      render: (row) => row.assigned_to_name || "Unassigned",
    },
    {
      key: "due_date",
      label: "Due Date",
      sortable: true,
      render: (row) => {
        if (!row.due_date) return "—";
        const due = new Date(row.due_date + "T00:00:00");
        const isOverdue = row.status === "OPEN" && due < new Date();
        return (
          <span className={isOverdue ? "text-red-600 font-medium" : ""}>
            {due.toLocaleDateString()}
          </span>
        );
      },
    },
    {
      key: "days_open",
      label: "Days",
      render: (row) => row.days_open ?? "—",
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

  const hasData = MOCK_RFIS.length > 0;

  return (
    <div>
      <PageHeader
        title="RFIs"
        subtitle="Manage requests for information"
        action={
          <button
            onClick={() => router.push(`/app/projects/${projectId}/rfis/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2 w-full sm:w-auto justify-center"
          >
            <Plus className="h-4 w-4" />
            New RFI
          </button>
        }
      />

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search RFIs..."
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
                  { label: "Responded", value: "RESPONDED" },
                  { label: "Closed", value: "CLOSED" },
                ],
              },
              {
                key: "priority",
                label: "All Priorities",
                value: priorityFilter,
                onChange: setPriorityFilter,
                options: [
                  { label: "Urgent", value: "URGENT" },
                  { label: "High", value: "HIGH" },
                  { label: "Normal", value: "NORMAL" },
                  { label: "Low", value: "LOW" },
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
            onRowClick={(row) => router.push(`/app/projects/${projectId}/rfis/${row.id}`)}
            page={page}
            totalPages={1}
            total={filtered.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={HelpCircle}
          title="No RFIs yet"
          description="Create your first RFI to start tracking requests for information."
          actionLabel="Create RFI"
          onAction={() => router.push(`/app/projects/${projectId}/rfis/new`)}
        />
      )}
    </div>
  );
}
