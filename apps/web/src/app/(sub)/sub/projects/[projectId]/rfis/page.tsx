"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, HelpCircle, MessageSquare } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { RFI } from "@/types/rfi";

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
];

export default function SubRFIsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState("number");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_RFIS;
  if (statusFilter) filtered = filtered.filter((r) => r.status === statusFilter);
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
      render: (row) => <span className="font-medium truncate block max-w-xs">{row.subject}</span>,
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
      render: (row) => <span className="text-sm">{row.priority}</span>,
    },
    {
      key: "due_date",
      label: "Due Date",
      sortable: true,
      render: (row) => (row.due_date ? new Date(row.due_date + "T00:00:00").toLocaleDateString() : "—"),
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
        subtitle="View and respond to requests for information"
        action={
          <button
            onClick={() => router.push(`/sub/projects/${projectId}/rfis/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
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
            ]}
          />
          <DataTable
            columns={columns}
            data={filtered}
            sortKey={sortKey}
            sortOrder={sortOrder}
            onSort={handleSort}
            onRowClick={(row) => router.push(`/sub/projects/${projectId}/rfis/${row.id}`)}
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
          description="RFIs assigned to you will appear here."
          actionLabel="Create RFI"
          onAction={() => router.push(`/sub/projects/${projectId}/rfis/new`)}
        />
      )}
    </div>
  );
}
