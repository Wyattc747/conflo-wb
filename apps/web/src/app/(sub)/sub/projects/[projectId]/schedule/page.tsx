"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Calendar } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import type { ScheduleTask } from "@/types/schedule";

const MOCK_TASKS: ScheduleTask[] = [
  {
    id: "3",
    project_id: "p1",
    name: "Structural steel erection - Level 1",
    wbs_code: "2.1",
    parent_task_id: null,
    sort_order: 1,
    start_date: "2026-03-10",
    end_date: "2026-03-28",
    duration: 15,
    sub_start_date: "2026-03-10",
    sub_end_date: "2026-03-28",
    percent_complete: 0,
    actual_start: null,
    actual_end: null,
    assigned_to_sub_id: "sub1",
    milestone: false,
    is_critical: true,
    dependencies: [],
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-02-01T10:00:00Z",
  },
  {
    id: "6",
    project_id: "p1",
    name: "Structural steel erection - Level 2",
    wbs_code: "2.3",
    parent_task_id: null,
    sort_order: 2,
    start_date: "2026-04-01",
    end_date: "2026-04-18",
    duration: 14,
    sub_start_date: "2026-04-01",
    sub_end_date: "2026-04-18",
    percent_complete: 0,
    actual_start: null,
    actual_end: null,
    assigned_to_sub_id: "sub1",
    milestone: false,
    is_critical: true,
    dependencies: [{ id: "d4", predecessor_id: "3", dependency_type: "FS", lag_days: 2 }],
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-02-01T10:00:00Z",
  },
  {
    id: "7",
    project_id: "p1",
    name: "Steel punch list items",
    wbs_code: "2.4",
    parent_task_id: null,
    sort_order: 3,
    start_date: "2026-04-21",
    end_date: "2026-04-25",
    duration: 5,
    sub_start_date: "2026-04-21",
    sub_end_date: "2026-04-25",
    percent_complete: 0,
    actual_start: null,
    actual_end: null,
    assigned_to_sub_id: "sub1",
    milestone: false,
    is_critical: false,
    dependencies: [{ id: "d5", predecessor_id: "6", dependency_type: "FS", lag_days: 1 }],
    created_at: "2026-02-01T10:00:00Z",
    updated_at: "2026-02-01T10:00:00Z",
  },
];

export default function SubSchedulePage() {
  const params = useParams();
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
          {row.is_critical && (
            <span className="flex-shrink-0 w-1.5 h-4 bg-red-400 rounded-sm" />
          )}
          <span className="font-medium truncate">
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
        const date = row.sub_start_date || row.start_date;
        if (!date) return "—";
        return new Date(date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" });
      },
    },
    {
      key: "end_date",
      label: "End",
      sortable: true,
      render: (row) => {
        const date = row.sub_end_date || row.end_date;
        if (!date) return "—";
        return new Date(date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" });
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
        subtitle="View your scope in the project schedule"
      />

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
          description="Your scheduled tasks will appear here once the GC builds the project schedule."
        />
      )}
    </div>
  );
}
