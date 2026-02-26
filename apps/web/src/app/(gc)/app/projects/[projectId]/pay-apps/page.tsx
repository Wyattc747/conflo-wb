"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { Plus, Receipt, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatMoney } from "@/lib/money";
import { usePayApps } from "@/hooks/use-pay-apps";
import type { PayApp } from "@/types/pay-app";

export default function PayAppsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const { getToken } = useAuth();
  const [token, setToken] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState("number");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  useState(() => { getToken().then(setToken); });

  const { data, isLoading, error } = usePayApps("gc", projectId, token, {
    pay_app_type: typeFilter || undefined,
    status: statusFilter || undefined,
    page,
    per_page: 25,
  });

  const payApps = data?.data || [];
  const meta = data?.meta;

  const columns: Column<PayApp>[] = [
    {
      key: "formatted_number",
      label: "#",
      sortable: true,
      render: (row) => <span className="font-medium">{row.formatted_number}</span>,
    },
    {
      key: "pay_app_type",
      label: "Type",
      render: (row) => (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
          row.pay_app_type === "GC_TO_OWNER" ? "bg-blue-100 text-blue-800" : "bg-purple-100 text-purple-800"
        }`}>
          {row.pay_app_type === "GC_TO_OWNER" ? "GC \u2192 Owner" : "Sub \u2192 GC"}
        </span>
      ),
    },
    {
      key: "period",
      label: "Period",
      render: (row) => (
        <span className="text-sm">
          {new Date(row.period_from + "T00:00:00").toLocaleDateString()} \u2013 {new Date(row.period_to + "T00:00:00").toLocaleDateString()}
        </span>
      ),
    },
    {
      key: "sub_company_name",
      label: "Subcontractor",
      render: (row) => row.sub_company_name || "\u2014",
    },
    {
      key: "current_payment_due",
      label: "Current Due",
      sortable: true,
      className: "text-right",
      render: (row) => <span className="text-right block font-medium">{formatMoney(row.current_payment_due)}</span>,
    },
    {
      key: "contract_sum_to_date",
      label: "Contract Sum",
      className: "text-right",
      render: (row) => <span className="text-right block">{formatMoney(row.contract_sum_to_date)}</span>,
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

  if (isLoading) {
    return (
      <div>
        <PageHeader title="Pay Applications" subtitle="Manage payment applications and billing" />
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <PageHeader title="Pay Applications" subtitle="Manage payment applications and billing" />
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          Failed to load pay applications. Please try again.
        </div>
      </div>
    );
  }

  const hasData = payApps.length > 0 || typeFilter || statusFilter;

  return (
    <div>
      <PageHeader
        title="Pay Applications"
        subtitle="Manage payment applications and billing"
        action={
          <button
            onClick={() => router.push(`/app/projects/${projectId}/pay-apps/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Pay App
          </button>
        }
      />

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search pay apps..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[
              {
                key: "type",
                label: "All Types",
                value: typeFilter,
                onChange: setTypeFilter,
                options: [
                  { label: "GC \u2192 Owner", value: "GC_TO_OWNER" },
                  { label: "Sub \u2192 GC", value: "SUB_TO_GC" },
                ],
              },
              {
                key: "status",
                label: "All Statuses",
                value: statusFilter,
                onChange: setStatusFilter,
                options: [
                  { label: "Draft", value: "DRAFT" },
                  { label: "Submitted", value: "SUBMITTED" },
                  { label: "Approved", value: "APPROVED" },
                  { label: "Rejected", value: "REJECTED" },
                ],
              },
            ]}
          />
          <DataTable
            columns={columns}
            data={payApps}
            sortKey={sortKey}
            sortOrder={sortOrder}
            onSort={handleSort}
            onRowClick={(row) => router.push(`/app/projects/${projectId}/pay-apps/${row.id}`)}
            page={page}
            totalPages={meta?.total_pages ?? 1}
            total={meta?.total ?? payApps.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={Receipt}
          title="No pay applications yet"
          description="Create your first pay application to start the billing process."
          actionLabel="Create Pay App"
          onAction={() => router.push(`/app/projects/${projectId}/pay-apps/new`)}
        />
      )}
    </div>
  );
}
