"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, Package, Users } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { BidPackage } from "@/types/bid-package";

const MOCK_BID_PACKAGES: BidPackage[] = [
  {
    id: "1",
    project_id: "p1",
    number: 1,
    formatted_number: "BP-001",
    title: "Structural Steel Fabrication & Erection",
    description: "Complete structural steel package for levels 1-4 including connections.",
    trade: "Metals",
    trades: ["Metals"],
    status: "PUBLISHED",
    bid_due_date: "2026-03-15",
    pre_bid_meeting_date: "2026-03-05",
    estimated_value_cents: 85000000,
    requirements: "Must include shop drawings timeline.",
    scope_documents: [],
    invited_sub_ids: ["sub1", "sub2", "sub3"],
    submission_count: 2,
    awarded_sub_id: null,
    awarded_at: null,
    created_by_name: "John Smith",
    created_at: "2026-02-10T10:00:00Z",
    updated_at: "2026-02-20T10:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    number: 2,
    formatted_number: "BP-002",
    title: "HVAC Mechanical Systems",
    description: "Full HVAC scope including ductwork, equipment, and controls.",
    trade: "HVAC",
    trades: ["HVAC"],
    status: "CLOSED",
    bid_due_date: "2026-02-28",
    estimated_value_cents: 120000000,
    requirements: null,
    scope_documents: [],
    invited_sub_ids: ["sub4", "sub5"],
    submission_count: 2,
    awarded_sub_id: null,
    awarded_at: null,
    created_by_name: "John Smith",
    created_at: "2026-02-05T09:00:00Z",
    updated_at: "2026-02-28T17:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    number: 3,
    formatted_number: "BP-003",
    title: "Electrical Systems",
    description: "Complete electrical package including power, lighting, and low voltage.",
    trade: "Electrical",
    trades: ["Electrical", "Low Voltage"],
    status: "AWARDED",
    bid_due_date: "2026-02-20",
    estimated_value_cents: 95000000,
    requirements: null,
    scope_documents: [],
    invited_sub_ids: ["sub6", "sub7", "sub8"],
    submission_count: 3,
    awarded_sub_id: "sub7",
    awarded_at: "2026-02-25T14:00:00Z",
    created_by_name: "Sarah Johnson",
    created_at: "2026-02-01T08:00:00Z",
    updated_at: "2026-02-25T14:00:00Z",
  },
  {
    id: "4",
    project_id: "p1",
    number: 4,
    formatted_number: "BP-004",
    title: "Concrete Foundations & Slabs",
    description: "All concrete work including footings, grade beams, and elevated slabs.",
    trade: "Concrete",
    trades: ["Concrete"],
    status: "DRAFT",
    bid_due_date: "2026-03-25",
    estimated_value_cents: 65000000,
    requirements: null,
    scope_documents: [],
    invited_sub_ids: [],
    submission_count: 0,
    awarded_sub_id: null,
    awarded_at: null,
    created_by_name: "John Smith",
    created_at: "2026-02-22T11:00:00Z",
    updated_at: "2026-02-22T11:00:00Z",
  },
];

function formatMoney(cents: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0 }).format(cents / 100);
}

export default function BidPackagesPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState("number");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_BID_PACKAGES;
  if (statusFilter) filtered = filtered.filter((b) => b.status === statusFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (b) =>
        b.title.toLowerCase().includes(s) ||
        b.formatted_number.toLowerCase().includes(s) ||
        (b.trade && b.trade.toLowerCase().includes(s))
    );
  }

  const columns: Column<BidPackage>[] = [
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
      render: (row) => (
        <div>
          <span className="font-medium truncate block max-w-xs">{row.title}</span>
          {row.trade && <span className="text-xs text-gray-500">{row.trade}</span>}
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
      key: "estimated_value_cents",
      label: "Est. Value",
      sortable: true,
      render: (row) => (
        <span className="text-sm font-medium">
          {row.estimated_value_cents ? formatMoney(row.estimated_value_cents) : "\u2014"}
        </span>
      ),
    },
    {
      key: "bid_due_date",
      label: "Bid Due",
      sortable: true,
      render: (row) => {
        if (!row.bid_due_date) return "\u2014";
        const due = new Date(row.bid_due_date + "T00:00:00");
        const isOverdue = row.status === "PUBLISHED" && due < new Date();
        return (
          <span className={isOverdue ? "text-red-600 font-medium" : ""}>
            {due.toLocaleDateString()}
          </span>
        );
      },
    },
    {
      key: "submission_count",
      label: "Bids",
      render: (row) => (
        <span className="flex items-center gap-1 text-sm">
          <Users className="h-3.5 w-3.5 text-gray-400" />
          {row.submission_count} / {row.invited_sub_ids.length}
        </span>
      ),
    },
    {
      key: "created_by_name",
      label: "Created By",
      render: (row) => row.created_by_name || "\u2014",
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

  const hasData = MOCK_BID_PACKAGES.length > 0;

  return (
    <div>
      <PageHeader
        title="Bid Packages"
        subtitle="Create and manage bid packages for subcontractors"
        action={
          <button
            onClick={() => router.push(`/app/projects/${projectId}/bid-packages/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2 w-full sm:w-auto justify-center"
          >
            <Plus className="h-4 w-4" />
            New Bid Package
          </button>
        }
      />

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search bid packages..."
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
                  { label: "Published", value: "PUBLISHED" },
                  { label: "Closed", value: "CLOSED" },
                  { label: "Awarded", value: "AWARDED" },
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
            onRowClick={(row) => router.push(`/app/projects/${projectId}/bid-packages/${row.id}`)}
            page={page}
            totalPages={1}
            total={filtered.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={Package}
          title="No bid packages yet"
          description="Create your first bid package to start collecting bids from subcontractors."
          actionLabel="Create Bid Package"
          onAction={() => router.push(`/app/projects/${projectId}/bid-packages/new`)}
        />
      )}
    </div>
  );
}
