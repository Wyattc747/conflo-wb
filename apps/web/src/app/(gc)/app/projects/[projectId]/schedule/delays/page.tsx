"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Plus, Clock, CheckCircle, XCircle } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { ScheduleDelay } from "@/types/schedule";

const MOCK_DELAYS: ScheduleDelay[] = [
  {
    id: "1",
    project_id: "p1",
    task_ids: ["1"],
    delay_days: 2,
    reason_category: "WEATHER",
    responsible_party: "OWNER",
    description: "Heavy rain prevented excavation work for 2 consecutive days. Soil too saturated to continue safely.",
    impacts_gc_schedule: true,
    impacts_owner_schedule: true,
    impacts_sub_schedule: true,
    status: "APPROVED",
    approved_by: "u1",
    approved_at: "2026-02-19T10:00:00Z",
    applied_at: "2026-02-19T10:30:00Z",
    created_by: "u2",
    created_at: "2026-02-18T08:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    task_ids: ["2"],
    delay_days: 1,
    reason_category: "MATERIAL_DELAY",
    responsible_party: "SUBCONTRACTOR",
    description: "Rebar delivery delayed by 1 day due to supplier production issue.",
    impacts_gc_schedule: true,
    impacts_owner_schedule: false,
    impacts_sub_schedule: true,
    status: "APPROVED",
    approved_by: "u1",
    approved_at: "2026-02-24T14:00:00Z",
    applied_at: null,
    created_by: "u2",
    created_at: "2026-02-24T09:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    task_ids: ["3"],
    delay_days: 3,
    reason_category: "DESIGN_CHANGE",
    responsible_party: "OWNER",
    description: "Owner requested steel connection redesign at grid B/4. Waiting for revised structural drawings before fabrication can proceed.",
    impacts_gc_schedule: true,
    impacts_owner_schedule: true,
    impacts_sub_schedule: true,
    rfi_id: "rfi-1",
    status: "PENDING",
    approved_by: null,
    approved_at: null,
    applied_at: null,
    created_by: "u3",
    created_at: "2026-02-25T11:00:00Z",
  },
  {
    id: "4",
    project_id: "p1",
    task_ids: ["5"],
    delay_days: 2,
    reason_category: "LABOR_SHORTAGE",
    responsible_party: "SUBCONTRACTOR",
    description: "MEP sub unable to staff crew for 2 days due to another project obligation.",
    impacts_gc_schedule: false,
    impacts_owner_schedule: false,
    impacts_sub_schedule: true,
    status: "REJECTED",
    approved_by: null,
    approved_at: null,
    applied_at: null,
    created_by: "u3",
    created_at: "2026-02-23T15:00:00Z",
  },
];

const totalDelayDays = MOCK_DELAYS.filter((d) => d.status === "APPROVED").reduce((sum, d) => sum + d.delay_days, 0);
const pendingDelayDays = MOCK_DELAYS.filter((d) => d.status === "PENDING").reduce((sum, d) => sum + d.delay_days, 0);

export default function ScheduleDelaysPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_DELAYS;
  if (statusFilter) filtered = filtered.filter((d) => d.status === statusFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter((d) => d.description.toLowerCase().includes(s) || d.reason_category.toLowerCase().includes(s));
  }

  const columns: Column<ScheduleDelay>[] = [
    {
      key: "created_at",
      label: "Date",
      sortable: true,
      className: "w-28",
      render: (row) => (
        <span className="text-sm">{new Date(row.created_at).toLocaleDateString()}</span>
      ),
    },
    {
      key: "delay_days",
      label: "Days",
      sortable: true,
      className: "w-20",
      render: (row) => (
        <span className="font-semibold text-red-600">+{row.delay_days}</span>
      ),
    },
    {
      key: "reason_category",
      label: "Reason",
      sortable: true,
      render: (row) => (
        <span className="text-sm">{row.reason_category.replace(/_/g, " ")}</span>
      ),
    },
    {
      key: "responsible_party",
      label: "Responsible",
      render: (row) => (
        <span className="text-sm">{row.responsible_party.replace(/_/g, " ")}</span>
      ),
    },
    {
      key: "description",
      label: "Description",
      className: "max-w-xs",
      render: (row) => (
        <span className="text-sm text-gray-600 truncate block max-w-xs">{row.description}</span>
      ),
    },
    {
      key: "task_ids",
      label: "Tasks",
      className: "w-20",
      render: (row) => (
        <span className="text-sm text-gray-500">{row.task_ids.length}</span>
      ),
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: "actions",
      label: "",
      className: "w-24",
      render: (row) =>
        row.status === "PENDING" ? (
          <div className="flex items-center gap-1">
            <button
              onClick={(e) => { e.stopPropagation(); console.log("approve", row.id); }}
              className="p-1 rounded hover:bg-green-100"
              title="Approve"
            >
              <CheckCircle className="h-4 w-4 text-green-600" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); console.log("reject", row.id); }}
              className="p-1 rounded hover:bg-red-100"
              title="Reject"
            >
              <XCircle className="h-4 w-4 text-red-600" />
            </button>
          </div>
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

  const hasData = MOCK_DELAYS.length > 0;

  return (
    <div>
      <PageHeader
        title={
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push(`/app/projects/${projectId}/schedule`)}
              className="p-1 rounded hover:bg-gray-200"
            >
              <ArrowLeft className="h-5 w-5 text-gray-500" />
            </button>
            <span>Schedule Delays</span>
          </div>
        }
        subtitle="Track and manage schedule delay claims"
        action={
          <button
            onClick={() => console.log("log delay")}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Log Delay
          </button>
        }
      />

      {/* Summary Bar */}
      {hasData && (
        <div className="grid grid-cols-3 gap-4 mb-5">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Approved Delay Days</div>
            <div className="text-2xl font-bold text-red-600 mt-1">{totalDelayDays}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Pending Delay Days</div>
            <div className="text-2xl font-bold text-yellow-600 mt-1">{pendingDelayDays}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Total Claims</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{MOCK_DELAYS.length}</div>
          </div>
        </div>
      )}

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search delays..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[
              {
                key: "status",
                label: "All Statuses",
                value: statusFilter,
                onChange: setStatusFilter,
                options: [
                  { label: "Pending", value: "PENDING" },
                  { label: "Approved", value: "APPROVED" },
                  { label: "Rejected", value: "REJECTED" },
                  { label: "Applied", value: "APPLIED" },
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
            page={page}
            totalPages={1}
            total={filtered.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={Clock}
          title="No delays logged"
          description="Schedule delays will be logged here when they occur."
          actionLabel="Log Delay"
          onAction={() => console.log("log delay")}
        />
      )}
    </div>
  );
}
