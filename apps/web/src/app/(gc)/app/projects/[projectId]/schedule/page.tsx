"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, Calendar, Lock, Upload, Clock, AlertTriangle } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import type { ScheduleTask } from "@/types/schedule";

const HEALTH_STYLES: Record<string, string> = {
  ON_TRACK: "bg-green-100 text-green-700",
  AT_RISK: "bg-yellow-100 text-yellow-700",
  BEHIND: "bg-red-100 text-red-700",
};

const MOCK_HEALTH = {
  status: "AT_RISK",
  slippage_days: 3,
  on_track_threshold: 2,
  at_risk_threshold: 7,
};

const MOCK_TASKS: ScheduleTask[] = [
  {
    id: "1",
    project_id: "p1",
    name: "Foundation excavation",
    description: "Excavate for spread footings on grids A-F",
    wbs_code: "1.1",
    parent_task_id: null,
    sort_order: 1,
    start_date: "2026-02-10",
    end_date: "2026-02-21",
    duration: 10,
    baseline_start: "2026-02-10",
    baseline_end: "2026-02-19",
    baseline_duration: 8,
    percent_complete: 100,
    actual_start: "2026-02-10",
    actual_end: "2026-02-21",
    assigned_to: "u2",
    milestone: false,
    is_critical: true,
    dependencies: [],
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-02-21T16:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    name: "Foundation concrete pour",
    description: "Pour spread footings and grade beams",
    wbs_code: "1.2",
    parent_task_id: null,
    sort_order: 2,
    start_date: "2026-02-24",
    end_date: "2026-03-07",
    duration: 10,
    baseline_start: "2026-02-21",
    baseline_end: "2026-03-04",
    baseline_duration: 10,
    percent_complete: 40,
    actual_start: "2026-02-24",
    actual_end: null,
    assigned_to: "u2",
    milestone: false,
    is_critical: true,
    dependencies: [{ id: "d1", predecessor_id: "1", dependency_type: "FS", lag_days: 1 }],
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-02-25T12:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    name: "Structural steel erection - Level 1",
    description: "Erect structural steel for Level 1 framing",
    wbs_code: "2.1",
    parent_task_id: null,
    sort_order: 3,
    start_date: "2026-03-10",
    end_date: "2026-03-28",
    duration: 15,
    baseline_start: "2026-03-07",
    baseline_end: "2026-03-25",
    baseline_duration: 15,
    percent_complete: 0,
    actual_start: null,
    actual_end: null,
    assigned_to: "u3",
    assigned_to_sub_id: "sub1",
    milestone: false,
    is_critical: true,
    dependencies: [{ id: "d2", predecessor_id: "2", dependency_type: "FS", lag_days: 2 }],
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-02-01T10:00:00Z",
  },
  {
    id: "4",
    project_id: "p1",
    name: "Level 1 framing complete",
    wbs_code: "2.2",
    parent_task_id: null,
    sort_order: 4,
    start_date: "2026-03-28",
    end_date: "2026-03-28",
    duration: 0,
    baseline_start: "2026-03-25",
    baseline_end: "2026-03-25",
    baseline_duration: 0,
    percent_complete: 0,
    actual_start: null,
    actual_end: null,
    milestone: true,
    is_critical: true,
    dependencies: [{ id: "d3", predecessor_id: "3", dependency_type: "FS", lag_days: 0 }],
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-02-01T10:00:00Z",
  },
  {
    id: "5",
    project_id: "p1",
    name: "MEP rough-in - Level 1",
    wbs_code: "3.1",
    parent_task_id: null,
    sort_order: 5,
    start_date: "2026-03-17",
    end_date: "2026-04-07",
    duration: 16,
    baseline_start: "2026-03-14",
    baseline_end: "2026-04-04",
    baseline_duration: 16,
    percent_complete: 0,
    actual_start: null,
    actual_end: null,
    assigned_to: "u3",
    milestone: false,
    is_critical: false,
    dependencies: [],
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-02-01T10:00:00Z",
  },
];

export default function SchedulePage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState("sort_order");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_TASKS;
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter((t) => t.name.toLowerCase().includes(s));
  }

  const columns: Column<ScheduleTask>[] = [
    {
      key: "name",
      label: "Task Name",
      sortable: true,
      className: "max-w-sm",
      render: (row) => (
        <div className="flex items-center gap-2">
          {row.milestone && (
            <span className="flex-shrink-0 w-2.5 h-2.5 bg-[#2E75B6] rotate-45" />
          )}
          {row.is_critical && !row.milestone && (
            <span className="flex-shrink-0 w-1.5 h-4 bg-red-400 rounded-sm" />
          )}
          <span className={`font-medium truncate ${row.milestone ? "text-[#2E75B6]" : ""}`}>
            {row.wbs_code && <span className="text-gray-400 font-mono mr-2">{row.wbs_code}</span>}
            {row.name}
          </span>
        </div>
      ),
    },
    {
      key: "start_date",
      label: "Start",
      sortable: true,
      render: (row) => {
        if (!row.start_date) return "—";
        const start = new Date(row.start_date + "T00:00:00");
        const isLate = row.baseline_start && row.start_date > row.baseline_start;
        return (
          <span className={isLate ? "text-red-600" : ""}>
            {start.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
          </span>
        );
      },
    },
    {
      key: "end_date",
      label: "End",
      sortable: true,
      render: (row) => {
        if (!row.end_date) return "—";
        const end = new Date(row.end_date + "T00:00:00");
        const isLate = row.baseline_end && row.end_date > row.baseline_end;
        return (
          <span className={isLate ? "text-red-600" : ""}>
            {end.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
          </span>
        );
      },
    },
    {
      key: "duration",
      label: "Duration",
      render: (row) => (
        <span className="text-sm text-gray-600">
          {row.duration != null ? `${row.duration}d` : "—"}
        </span>
      ),
    },
    {
      key: "percent_complete",
      label: "%",
      sortable: true,
      className: "w-28",
      render: (row) => (
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${row.percent_complete === 100 ? "bg-green-500" : "bg-[#2E75B6]"}`}
              style={{ width: `${row.percent_complete}%` }}
            />
          </div>
          <span className="text-xs text-gray-500 w-8 text-right">{row.percent_complete}%</span>
        </div>
      ),
    },
    {
      key: "status",
      label: "Status",
      render: (row) => {
        if (row.percent_complete === 100) {
          return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">Complete</span>;
        }
        if (row.actual_start) {
          return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">In Progress</span>;
        }
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">Not Started</span>;
      },
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

  const hasData = MOCK_TASKS.length > 0;

  return (
    <div>
      <PageHeader
        title="Schedule"
        subtitle="Manage project schedule and milestones"
        action={
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push(`/app/projects/${projectId}/schedule/delays`)}
              className="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-2"
            >
              <Clock className="h-4 w-4" />
              Delays
            </button>
            <button
              onClick={() => router.push(`/app/projects/${projectId}/schedule/archive`)}
              className="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Archive
            </button>
            <button
              onClick={() => console.log("lock baseline")}
              className="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-2"
            >
              <Lock className="h-4 w-4" />
              Lock Baseline
            </button>
            <button
              onClick={() => console.log("publish")}
              className="bg-[#2E75B6] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#256099] flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Publish
            </button>
            <button
              onClick={() => console.log("add task")}
              className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Add Task
            </button>
          </div>
        }
      />

      {/* Health Badge */}
      {hasData && (
        <div className="mb-4 flex items-center gap-3">
          <span className={`px-3 py-1.5 rounded-lg text-sm font-semibold ${HEALTH_STYLES[MOCK_HEALTH.status] || ""}`}>
            {MOCK_HEALTH.status === "ON_TRACK" && "On Track"}
            {MOCK_HEALTH.status === "AT_RISK" && (
              <span className="flex items-center gap-1">
                <AlertTriangle className="h-3.5 w-3.5" />
                At Risk
              </span>
            )}
            {MOCK_HEALTH.status === "BEHIND" && (
              <span className="flex items-center gap-1">
                <AlertTriangle className="h-3.5 w-3.5" />
                Behind Schedule
              </span>
            )}
          </span>
          {MOCK_HEALTH.slippage_days > 0 && (
            <span className="text-sm text-gray-500">
              {MOCK_HEALTH.slippage_days} day{MOCK_HEALTH.slippage_days !== 1 ? "s" : ""} behind baseline
            </span>
          )}
        </div>
      )}

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search tasks..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[]}
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
          icon={Calendar}
          title="No schedule items yet"
          description="Add your first task to start building the project schedule."
          actionLabel="Add Task"
          onAction={() => console.log("add task")}
        />
      )}
    </div>
  );
}
