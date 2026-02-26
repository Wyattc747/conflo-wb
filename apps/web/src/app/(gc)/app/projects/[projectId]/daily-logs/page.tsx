"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, ClipboardList, Cloud, Sun, CloudRain } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { DailyLog } from "@/types/daily-log";

// Mock data for UI development
const MOCK_LOGS: DailyLog[] = [
  {
    id: "1",
    project_id: "p1",
    log_date: "2026-02-25",
    number: "DL-2026-02-25",
    weather_data: { condition: "Sunny", temp_high: 72, temp_low: 45 },
    work_performed: "Poured concrete for footings on grid A-C. Steel erection continued on level 2.",
    manpower: [{ trade: "Concrete", workers: 8, hours: 64 }, { trade: "Ironworkers", workers: 6, hours: 48 }],
    status: "DRAFT",
    created_by_name: "John Smith",
    created_at: "2026-02-25T08:00:00Z",
    updated_at: "2026-02-25T16:30:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    log_date: "2026-02-24",
    number: "DL-2026-02-24",
    weather_data: { condition: "Cloudy", temp_high: 58, temp_low: 38 },
    work_performed: "Formwork layout for level 1 slab. MEP rough-in ongoing.",
    manpower: [{ trade: "Carpenters", workers: 5, hours: 40 }, { trade: "Plumbing", workers: 3, hours: 24 }],
    status: "SUBMITTED",
    created_by_name: "John Smith",
    created_at: "2026-02-24T08:00:00Z",
    updated_at: "2026-02-24T17:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    log_date: "2026-02-23",
    number: "DL-2026-02-23",
    weather_data: { condition: "Rain", temp_high: 50, temp_low: 35 },
    work_performed: "Rain delay — interior work only. Electrical rough-in on level 1.",
    delays_text: "Rain delay — 4 hours lost",
    manpower: [{ trade: "Electrical", workers: 4, hours: 16 }],
    status: "APPROVED",
    created_by_name: "Jane Doe",
    created_at: "2026-02-23T08:00:00Z",
    updated_at: "2026-02-23T15:00:00Z",
  },
];

function WeatherIcon({ condition }: { condition?: string }) {
  if (!condition) return null;
  const lower = condition.toLowerCase();
  if (lower.includes("rain")) return <CloudRain className="h-4 w-4 text-blue-500" />;
  if (lower.includes("cloud")) return <Cloud className="h-4 w-4 text-gray-400" />;
  return <Sun className="h-4 w-4 text-yellow-500" />;
}

function getTotalWorkers(manpower?: { trade: string; workers: number; hours: number }[] | null): number {
  if (!manpower) return 0;
  return manpower.reduce((sum, m) => sum + m.workers, 0);
}

export default function DailyLogsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState("log_date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  // Filter mock data
  let filtered = MOCK_LOGS;
  if (statusFilter) filtered = filtered.filter((l) => l.status === statusFilter);
  if (search) filtered = filtered.filter((l) => l.work_performed?.toLowerCase().includes(search.toLowerCase()));

  const columns: Column<DailyLog>[] = [
    {
      key: "log_date",
      label: "Date",
      sortable: true,
      render: (row) => (
        <span className="font-medium">{new Date(row.log_date + "T00:00:00").toLocaleDateString()}</span>
      ),
    },
    {
      key: "weather",
      label: "Weather",
      render: (row) => (
        <div className="flex items-center gap-1.5">
          <WeatherIcon condition={row.weather_data?.condition} />
          <span className="text-xs">
            {row.weather_data?.condition || "—"}
            {row.weather_data?.temp_high != null && (
              <span className="text-gray-400 ml-1">
                {row.weather_data.temp_high}°/{row.weather_data?.temp_low}°
              </span>
            )}
          </span>
        </div>
      ),
    },
    {
      key: "work_performed",
      label: "Work Performed",
      className: "max-w-xs",
      render: (row) => (
        <span className="truncate block max-w-xs">
          {row.work_performed || "—"}
        </span>
      ),
    },
    {
      key: "manpower",
      label: "Workers",
      render: (row) => getTotalWorkers(row.manpower) || "—",
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: "created_by_name",
      label: "Created By",
      render: (row) => row.created_by_name || "—",
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

  const hasData = MOCK_LOGS.length > 0;

  return (
    <div>
      <PageHeader
        title="Daily Logs"
        subtitle="Track daily project activity and conditions"
        action={
          <button
            onClick={() => router.push(`/app/projects/${projectId}/daily-logs/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Daily Log
          </button>
        }
      />

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search work performed..."
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
            onRowClick={(row) => router.push(`/app/projects/${projectId}/daily-logs/${row.id}`)}
            page={page}
            totalPages={1}
            total={filtered.length}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={ClipboardList}
          title="No daily logs yet"
          description="Create your first daily log to start tracking project activity."
          actionLabel="Create Daily Log"
          onAction={() => router.push(`/app/projects/${projectId}/daily-logs/new`)}
        />
      )}
    </div>
  );
}
