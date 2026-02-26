"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, BookOpen, MessageSquare } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { Submittal } from "@/types/submittal";

const TYPE_STYLES: Record<string, string> = {
  SHOP_DRAWING: "bg-blue-100 text-blue-700",
  PRODUCT_DATA: "bg-purple-100 text-purple-700",
  SAMPLE: "bg-green-100 text-green-700",
  MOCK_UP: "bg-orange-100 text-orange-700",
  OTHER: "bg-gray-100 text-gray-600",
};

const MOCK_SUBMITTALS: Submittal[] = [
  {
    id: "1",
    project_id: "p1",
    number: 1,
    revision: 0,
    formatted_number: "001.00",
    title: "Structural steel shop drawings - Level 2",
    spec_section: "05 12 00",
    submittal_type: "SHOP_DRAWING",
    status: "SUBMITTED",
    sub_company_id: "sub1",
    sub_company_name: "Apex Steel Fabricators",
    assigned_to: "u2",
    assigned_to_name: "Sarah Johnson",
    due_date: "2026-03-10",
    days_open: 8,
    lead_time_days: 21,
    revision_history: [],
    comments_count: 2,
    created_by_name: "John Smith",
    created_at: "2026-02-18T10:00:00Z",
    updated_at: "2026-02-20T10:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    number: 2,
    revision: 1,
    formatted_number: "002.01",
    title: "HVAC ductwork product data",
    spec_section: "23 31 00",
    submittal_type: "PRODUCT_DATA",
    status: "REVISE_AND_RESUBMIT",
    sub_company_id: "sub2",
    sub_company_name: "Summit Mechanical",
    assigned_to: "u3",
    assigned_to_name: "Mike Chen",
    due_date: "2026-03-05",
    days_open: null,
    lead_time_days: 14,
    review_notes: "Duct gauge does not meet spec requirement. Resubmit with 20-gauge per spec 23 31 00.",
    reviewed_by_name: "Mike Chen",
    reviewed_at: "2026-02-24T15:00:00Z",
    revision_history: [
      { revision: 0, formatted_number: "002.00", status: "REVISE_AND_RESUBMIT", created_at: "2026-02-15T09:00:00Z", reviewed_at: "2026-02-20T14:00:00Z" },
    ],
    comments_count: 4,
    created_by_name: "Jane Doe",
    created_at: "2026-02-15T09:00:00Z",
    updated_at: "2026-02-24T15:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    number: 3,
    revision: 0,
    formatted_number: "003.00",
    title: "Exterior brick sample panel",
    spec_section: "04 21 00",
    submittal_type: "SAMPLE",
    status: "APPROVED",
    sub_company_id: "sub3",
    sub_company_name: "Heritage Masonry",
    assigned_to: "u2",
    assigned_to_name: "Sarah Johnson",
    due_date: "2026-02-28",
    days_open: null,
    lead_time_days: 28,
    review_notes: "Sample approved. Proceed with ordering.",
    reviewed_by_name: "Sarah Johnson",
    reviewed_at: "2026-02-26T11:00:00Z",
    revision_history: [],
    comments_count: 1,
    created_by_name: "John Smith",
    created_at: "2026-02-10T08:00:00Z",
    updated_at: "2026-02-26T11:00:00Z",
  },
  {
    id: "4",
    project_id: "p1",
    number: 4,
    revision: 0,
    formatted_number: "004.00",
    title: "Curtain wall mock-up design",
    spec_section: "08 44 00",
    submittal_type: "MOCK_UP",
    status: "DRAFT",
    sub_company_id: "sub4",
    sub_company_name: "Precision Glass & Glazing",
    assigned_to: "u3",
    assigned_to_name: "Mike Chen",
    due_date: "2026-03-15",
    days_open: 3,
    lead_time_days: 35,
    revision_history: [],
    comments_count: 0,
    created_by_name: "John Smith",
    created_at: "2026-02-22T14:00:00Z",
    updated_at: "2026-02-22T14:00:00Z",
  },
];

export default function SubmittalsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [sortKey, setSortKey] = useState("number");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_SUBMITTALS;
  if (statusFilter) filtered = filtered.filter((s) => s.status === statusFilter);
  if (typeFilter) filtered = filtered.filter((s) => s.submittal_type === typeFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (item) =>
        item.title.toLowerCase().includes(s) ||
        item.formatted_number.toLowerCase().includes(s) ||
        (item.spec_section && item.spec_section.toLowerCase().includes(s))
    );
  }

  const columns: Column<Submittal>[] = [
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
      key: "submittal_type",
      label: "Type",
      sortable: true,
      render: (row) => (
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${TYPE_STYLES[row.submittal_type || "OTHER"]}`}>
          {(row.submittal_type || "OTHER").replace(/_/g, " ")}
        </span>
      ),
    },
    {
      key: "spec_section",
      label: "Spec Section",
      render: (row) => (
        <span className="font-mono text-sm text-gray-600">{row.spec_section || "—"}</span>
      ),
    },
    {
      key: "sub_company_name",
      label: "Sub",
      render: (row) => row.sub_company_name || "—",
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
        const isOverdue = !["APPROVED", "APPROVED_AS_NOTED", "REJECTED"].includes(row.status) && due < new Date();
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

  const hasData = MOCK_SUBMITTALS.length > 0;

  return (
    <div>
      <PageHeader
        title="Submittals"
        subtitle="Track and manage project submittals"
        action={
          <button
            onClick={() => router.push(`/app/projects/${projectId}/submittals/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Submittal
          </button>
        }
      />

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search submittals..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[
              {
                key: "status",
                label: "All Statuses",
                value: statusFilter,
                onChange: setStatusFilter,
                options: [
                  { label: "Draft", value: "DRAFT" },
                  { label: "Submitted", value: "SUBMITTED" },
                  { label: "Approved", value: "APPROVED" },
                  { label: "Approved as Noted", value: "APPROVED_AS_NOTED" },
                  { label: "Revise & Resubmit", value: "REVISE_AND_RESUBMIT" },
                  { label: "Rejected", value: "REJECTED" },
                ],
              },
              {
                key: "type",
                label: "All Types",
                value: typeFilter,
                onChange: setTypeFilter,
                options: [
                  { label: "Shop Drawing", value: "SHOP_DRAWING" },
                  { label: "Product Data", value: "PRODUCT_DATA" },
                  { label: "Sample", value: "SAMPLE" },
                  { label: "Mock-Up", value: "MOCK_UP" },
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
            onRowClick={(row) => router.push(`/app/projects/${projectId}/submittals/${row.id}`)}
            page={page}
            totalPages={1}
            total={filtered.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={BookOpen}
          title="No submittals yet"
          description="Create your first submittal to start the review process."
          actionLabel="Create Submittal"
          onAction={() => router.push(`/app/projects/${projectId}/submittals/new`)}
        />
      )}
    </div>
  );
}
