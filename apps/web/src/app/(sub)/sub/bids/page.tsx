"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Gavel, Clock } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { BidPackage } from "@/types/bid-package";

function formatMoney(cents: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0 }).format(cents / 100);
}

const MOCK_BID_PACKAGES: BidPackage[] = [
  {
    id: "1",
    project_id: "p1",
    number: 1,
    formatted_number: "BP-001",
    title: "Structural Steel Fabrication & Erection",
    description: "Complete structural steel package for levels 1-4.",
    trade: "Metals",
    trades: ["Metals"],
    status: "PUBLISHED",
    bid_due_date: "2026-03-15",
    pre_bid_meeting_date: "2026-03-05",
    estimated_value_cents: 85000000,
    requirements: "Must include shop drawings timeline.",
    scope_documents: [],
    invited_sub_ids: [],
    submission_count: 0,
    awarded_sub_id: null,
    awarded_at: null,
    created_by_name: "Apex Construction",
    created_at: "2026-02-10T10:00:00Z",
    updated_at: "2026-02-20T10:00:00Z",
  },
  {
    id: "2",
    project_id: "p2",
    number: 2,
    formatted_number: "BP-003",
    title: "Electrical Systems - Office Build-Out",
    description: "Complete electrical package for tenant improvement.",
    trade: "Electrical",
    trades: ["Electrical"],
    status: "PUBLISHED",
    bid_due_date: "2026-03-10",
    estimated_value_cents: 45000000,
    requirements: null,
    scope_documents: [],
    invited_sub_ids: [],
    submission_count: 0,
    awarded_sub_id: null,
    awarded_at: null,
    created_by_name: "Summit Builders",
    created_at: "2026-02-15T09:00:00Z",
    updated_at: "2026-02-15T09:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    number: 3,
    formatted_number: "BP-002",
    title: "HVAC Mechanical Systems",
    description: "Full HVAC scope including ductwork and controls.",
    trade: "HVAC",
    trades: ["HVAC"],
    status: "AWARDED",
    bid_due_date: "2026-02-28",
    estimated_value_cents: 120000000,
    requirements: null,
    scope_documents: [],
    invited_sub_ids: [],
    submission_count: 0,
    awarded_sub_id: "my-sub-id",
    awarded_at: "2026-03-01T14:00:00Z",
    created_by_name: "Apex Construction",
    created_at: "2026-02-05T09:00:00Z",
    updated_at: "2026-03-01T14:00:00Z",
  },
];

export default function SubBidsPage() {
  const router = useRouter();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState("bid_due_date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_BID_PACKAGES;
  if (statusFilter) filtered = filtered.filter((b) => b.status === statusFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (b) =>
        b.title.toLowerCase().includes(s) ||
        (b.trade && b.trade.toLowerCase().includes(s)) ||
        (b.created_by_name && b.created_by_name.toLowerCase().includes(s))
    );
  }

  const columns: Column<BidPackage>[] = [
    {
      key: "formatted_number",
      label: "#",
      sortable: true,
      className: "w-24",
      render: (row) => (
        <span className="font-mono text-sm font-medium text-[#1B2A4A]">{row.formatted_number}</span>
      ),
    },
    {
      key: "title",
      label: "Bid Package",
      sortable: true,
      className: "max-w-sm",
      render: (row) => (
        <div>
          <span className="font-medium truncate block max-w-sm">{row.title}</span>
          {row.trade && <span className="text-xs text-gray-500">{row.trade}</span>}
        </div>
      ),
    },
    {
      key: "created_by_name",
      label: "GC",
      render: (row) => row.created_by_name || "\u2014",
    },
    {
      key: "estimated_value_cents",
      label: "Est. Value",
      render: (row) => row.estimated_value_cents ? formatMoney(row.estimated_value_cents) : "\u2014",
    },
    {
      key: "bid_due_date",
      label: "Due Date",
      sortable: true,
      render: (row) => {
        if (!row.bid_due_date) return "\u2014";
        const due = new Date(row.bid_due_date + "T00:00:00");
        const isOverdue = row.status === "PUBLISHED" && due < new Date();
        const daysUntil = Math.ceil((due.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
        return (
          <div>
            <span className={isOverdue ? "text-red-600 font-medium" : ""}>
              {due.toLocaleDateString()}
            </span>
            {daysUntil > 0 && daysUntil <= 7 && row.status === "PUBLISHED" && (
              <span className="flex items-center gap-0.5 text-[10px] text-orange-600 mt-0.5">
                <Clock className="h-2.5 w-2.5" />{daysUntil}d left
              </span>
            )}
          </div>
        );
      },
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
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

  const hasData = MOCK_BID_PACKAGES.length > 0;
  const activeCount = MOCK_BID_PACKAGES.filter((b) => b.status === "PUBLISHED").length;

  return (
    <div>
      <PageHeader title="Bids" subtitle="View and respond to bid invitations" />

      {hasData && (
        <div className="grid grid-cols-3 gap-4 mb-5">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Total Invitations</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{MOCK_BID_PACKAGES.length}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Active</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">{activeCount}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Awarded</div>
            <div className="text-2xl font-bold text-green-600 mt-1">
              {MOCK_BID_PACKAGES.filter((b) => b.status === "AWARDED").length}
            </div>
          </div>
        </div>
      )}

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search bids..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[
              {
                key: "status",
                label: "All Statuses",
                value: statusFilter,
                onChange: setStatusFilter,
                options: [
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
            onRowClick={(row) => router.push(`/sub/bids/${row.id}`)}
            page={page}
            totalPages={1}
            total={filtered.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={Gavel}
          title="No active bids"
          description="Bid invitations will appear here when a GC sends you a bid package."
        />
      )}
    </div>
  );
}
