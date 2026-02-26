"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, Send, MessageSquare } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { Transmittal } from "@/types/transmittal";

const PURPOSE_STYLES: Record<string, string> = {
  FOR_APPROVAL: "bg-blue-100 text-blue-700",
  FOR_REVIEW: "bg-yellow-100 text-yellow-700",
  FOR_INFORMATION: "bg-gray-100 text-gray-600",
  FOR_RECORD: "bg-purple-100 text-purple-700",
  AS_REQUESTED: "bg-green-100 text-green-700",
};

const MOCK_TRANSMITTALS: Transmittal[] = [
  {
    id: "1",
    project_id: "p1",
    number: 1,
    formatted_number: "TR-001",
    subject: "Revised structural drawings - Set 3",
    to_company: "Heritage Masonry",
    to_contact: "Tom Baker",
    from_company: "ABC General Contractors",
    from_contact: "John Smith",
    purpose: "FOR_REVIEW",
    description: "Updated structural drawings incorporating RFI-001 response. Please review and confirm receipt.",
    status: "SENT",
    items: [
      { description: "S-201 Rev 3", quantity: 2, document_type: "Drawing" },
      { description: "S-202 Rev 3", quantity: 2, document_type: "Drawing" },
    ],
    sent_via: "EMAIL",
    sent_at: "2026-02-20T14:00:00Z",
    due_date: "2026-03-01",
    comments_count: 1,
    created_by_name: "John Smith",
    created_at: "2026-02-20T13:00:00Z",
    updated_at: "2026-02-20T14:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    number: 2,
    formatted_number: "TR-002",
    subject: "HVAC equipment submittals to architect",
    to_company: "Architectural Design Group",
    to_contact: "Lisa Park",
    from_company: "ABC General Contractors",
    from_contact: "Sarah Johnson",
    purpose: "FOR_APPROVAL",
    description: "Forwarding HVAC submittals for architect review and approval.",
    status: "ACKNOWLEDGED",
    items: [
      { description: "Submittal 002.01 - HVAC Ductwork", quantity: 1, document_type: "Submittal" },
    ],
    sent_via: "EMAIL",
    sent_at: "2026-02-18T10:00:00Z",
    received_at: "2026-02-19T09:30:00Z",
    due_date: "2026-02-25",
    comments_count: 2,
    created_by_name: "Sarah Johnson",
    created_at: "2026-02-18T09:00:00Z",
    updated_at: "2026-02-19T09:30:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    number: 3,
    formatted_number: "TR-003",
    subject: "Concrete test reports - February 2026",
    to_company: "Owner Development Corp",
    to_contact: "Robert Kim",
    from_company: "ABC General Contractors",
    from_contact: "Mike Chen",
    purpose: "FOR_RECORD",
    description: "Monthly concrete test reports for project records.",
    status: "DRAFT",
    items: [
      { description: "Concrete Break Test Report - Feb Week 1", quantity: 1, document_type: "Report" },
      { description: "Concrete Break Test Report - Feb Week 2", quantity: 1, document_type: "Report" },
      { description: "Concrete Break Test Report - Feb Week 3", quantity: 1, document_type: "Report" },
    ],
    sent_via: "HAND_DELIVERY",
    due_date: "2026-03-05",
    comments_count: 0,
    created_by_name: "Mike Chen",
    created_at: "2026-02-24T11:00:00Z",
    updated_at: "2026-02-24T11:00:00Z",
  },
];

export default function TransmittalsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [purposeFilter, setPurposeFilter] = useState("");
  const [sortKey, setSortKey] = useState("number");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_TRANSMITTALS;
  if (statusFilter) filtered = filtered.filter((t) => t.status === statusFilter);
  if (purposeFilter) filtered = filtered.filter((t) => t.purpose === purposeFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (t) =>
        t.subject.toLowerCase().includes(s) ||
        t.formatted_number.toLowerCase().includes(s) ||
        (t.to_company && t.to_company.toLowerCase().includes(s))
    );
  }

  const columns: Column<Transmittal>[] = [
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
      key: "to_company",
      label: "To Company",
      render: (row) => row.to_company || "—",
    },
    {
      key: "purpose",
      label: "Purpose",
      sortable: true,
      render: (row) => (
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PURPOSE_STYLES[row.purpose] || "bg-gray-100 text-gray-600"}`}>
          {row.purpose.replace(/_/g, " ")}
        </span>
      ),
    },
    {
      key: "sent_via",
      label: "Sent Via",
      render: (row) => (
        <span className="text-sm text-gray-600">{row.sent_via.replace(/_/g, " ")}</span>
      ),
    },
    {
      key: "due_date",
      label: "Due Date",
      sortable: true,
      render: (row) => {
        if (!row.due_date) return "—";
        const due = new Date(row.due_date + "T00:00:00");
        const isOverdue = row.status === "SENT" && due < new Date();
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

  const hasData = MOCK_TRANSMITTALS.length > 0;

  return (
    <div>
      <PageHeader
        title="Transmittals"
        subtitle="Send and track document transmittals"
        action={
          <button
            onClick={() => router.push(`/app/projects/${projectId}/transmittals/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Transmittal
          </button>
        }
      />

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search transmittals..."
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
                  { label: "Sent", value: "SENT" },
                  { label: "Acknowledged", value: "ACKNOWLEDGED" },
                ],
              },
              {
                key: "purpose",
                label: "All Purposes",
                value: purposeFilter,
                onChange: setPurposeFilter,
                options: [
                  { label: "For Approval", value: "FOR_APPROVAL" },
                  { label: "For Review", value: "FOR_REVIEW" },
                  { label: "For Information", value: "FOR_INFORMATION" },
                  { label: "For Record", value: "FOR_RECORD" },
                  { label: "As Requested", value: "AS_REQUESTED" },
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
            onRowClick={(row) => router.push(`/app/projects/${projectId}/transmittals/${row.id}`)}
            page={page}
            totalPages={1}
            total={filtered.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={Send}
          title="No transmittals yet"
          description="Create your first transmittal to send documents."
          actionLabel="Create Transmittal"
          onAction={() => router.push(`/app/projects/${projectId}/transmittals/new`)}
        />
      )}
    </div>
  );
}
