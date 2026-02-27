"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { Plus, FileText, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatMoney } from "@/lib/money";
import { useChangeOrders } from "@/hooks/use-change-orders";
import type { ChangeOrder } from "@/types/change-order";

function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    HIGH: "bg-red-100 text-red-800",
    URGENT: "bg-red-200 text-red-900",
    NORMAL: "bg-gray-100 text-gray-700",
    LOW: "bg-blue-100 text-blue-700",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors[priority] || colors.NORMAL}`}>
      {priority}
    </span>
  );
}

export default function ChangeOrdersPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const { getToken } = useAuth();
  const [token, setToken] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [sortKey, setSortKey] = useState("number");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  useState(() => { getToken().then(setToken); });

  const { data, isLoading, error } = useChangeOrders("gc", projectId, token, {
    status: statusFilter || undefined,
    priority: priorityFilter || undefined,
    search: search || undefined,
    sort: sortKey,
    order: sortOrder,
    page,
    per_page: 25,
  });

  const cos = data?.data || [];
  const meta = data?.meta;

  const columns: Column<ChangeOrder>[] = [
    {
      key: "formatted_number",
      label: "#",
      sortable: true,
      render: (row) => <span className="font-medium font-mono">{row.formatted_number}</span>,
    },
    {
      key: "title",
      label: "Title",
      sortable: true,
      className: "max-w-xs",
      render: (row) => <span className="truncate block max-w-xs">{row.title}</span>,
    },
    {
      key: "reason",
      label: "Reason",
      render: (row) => <span className="text-sm text-gray-600">{(row.reason || "").replace(/_/g, " ")}</span>,
    },
    {
      key: "gc_amount",
      label: "Amount",
      sortable: true,
      className: "text-right",
      render: (row) => (
        <span className="text-right block font-medium">
          {row.gc_amount ? formatMoney(row.gc_amount) : "TBD"}
        </span>
      ),
    },
    {
      key: "schedule_impact_days",
      label: "Schedule",
      render: (row) => (
        <span className={row.schedule_impact_days > 0 ? "text-amber-700" : "text-gray-400"}>
          {row.schedule_impact_days > 0 ? `+${row.schedule_impact_days}d` : "\u2014"}
        </span>
      ),
    },
    {
      key: "priority",
      label: "Priority",
      render: (row) => <PriorityBadge priority={row.priority} />,
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
      setSortOrder("desc");
    }
  };

  // Summary stats from loaded data
  const totalApproved = cos.filter((co) => co.status === "APPROVED").reduce((sum, co) => sum + co.gc_amount, 0);
  const totalPending = cos.filter((co) => !["APPROVED", "REJECTED"].includes(co.status)).reduce((sum, co) => sum + co.gc_amount, 0);

  if (isLoading) {
    return (
      <div>
        <PageHeader title="Change Orders" subtitle="Track and manage project change orders" />
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <PageHeader title="Change Orders" subtitle="Track and manage project change orders" />
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          Failed to load change orders. Please try again.
        </div>
      </div>
    );
  }

  const hasData = cos.length > 0 || statusFilter || priorityFilter || search;

  return (
    <div>
      <PageHeader
        title="Change Orders"
        subtitle="Track and manage project change orders"
        action={
          <button
            onClick={() => router.push(`/app/projects/${projectId}/change-orders/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2 w-full sm:w-auto justify-center"
          >
            <Plus className="h-4 w-4" />
            New Change Order
          </button>
        }
      />

      {hasData ? (
        <>
          {/* Summary bar */}
          <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-3 sm:mb-4">
            <div className="bg-white rounded-lg border border-gray-200 px-3 sm:px-4 py-2.5 sm:py-3">
              <p className="text-[10px] sm:text-xs text-gray-500 uppercase">Total Approved</p>
              <p className="text-base sm:text-lg font-semibold text-green-700">{formatMoney(totalApproved)}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 px-3 sm:px-4 py-2.5 sm:py-3">
              <p className="text-[10px] sm:text-xs text-gray-500 uppercase">Pending</p>
              <p className="text-base sm:text-lg font-semibold text-amber-700">{formatMoney(totalPending)}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 px-3 sm:px-4 py-2.5 sm:py-3">
              <p className="text-[10px] sm:text-xs text-gray-500 uppercase">Total COs</p>
              <p className="text-base sm:text-lg font-semibold">{meta?.total ?? cos.length}</p>
            </div>
          </div>

          <FilterBar
            searchPlaceholder="Search change orders..."
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
                  { label: "Pricing Requested", value: "PRICING_REQUESTED" },
                  { label: "Pricing Complete", value: "PRICING_COMPLETE" },
                  { label: "Submitted to Owner", value: "SUBMITTED_TO_OWNER" },
                  { label: "Approved", value: "APPROVED" },
                  { label: "Rejected", value: "REJECTED" },
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
            data={cos}
            sortKey={sortKey}
            sortOrder={sortOrder}
            onSort={handleSort}
            onRowClick={(row) => router.push(`/app/projects/${projectId}/change-orders/${row.id}`)}
            page={page}
            totalPages={meta?.total_pages ?? 1}
            total={meta?.total ?? cos.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={FileText}
          title="No change orders yet"
          description="Create your first change order to track project changes."
          actionLabel="Create Change Order"
          onAction={() => router.push(`/app/projects/${projectId}/change-orders/new`)}
        />
      )}
    </div>
  );
}
