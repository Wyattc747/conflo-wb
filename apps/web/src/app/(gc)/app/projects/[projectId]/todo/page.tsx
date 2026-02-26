"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, CheckSquare, MessageSquare } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ViewToggle } from "@/components/shared/ViewToggle";
import { KanbanBoard } from "@/components/shared/KanbanBoard";
import type { Todo } from "@/types/todo";

const PRIORITY_STYLES: Record<string, string> = {
  URGENT: "text-red-600 font-semibold",
  HIGH: "text-orange-600 font-medium",
  NORMAL: "text-gray-600",
  LOW: "text-gray-400",
};

const MOCK_TODOS: Todo[] = [
  {
    id: "1",
    project_id: "p1",
    title: "Submit revised construction schedule",
    description: "Update the baseline schedule with approved change order impacts.",
    status: "OPEN",
    priority: "HIGH",
    assigned_to: "u2",
    assigned_to_name: "Sarah Johnson",
    due_date: "2026-03-01",
    category: "SCHEDULE",
    created_by_name: "John Smith",
    created_at: "2026-02-20T10:00:00Z",
    updated_at: "2026-02-20T10:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    title: "Obtain city electrical permit",
    description: "Apply for and obtain electrical permit from city building department.",
    status: "IN_PROGRESS",
    priority: "URGENT",
    assigned_to: "u3",
    assigned_to_name: "Mike Chen",
    due_date: "2026-02-28",
    category: "PERMITS",
    created_by_name: "John Smith",
    created_at: "2026-02-15T09:00:00Z",
    updated_at: "2026-02-22T14:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    title: "Review steel shop drawing submittal",
    description: "Review and comment on Apex Steel shop drawing submittal 001.00.",
    status: "COMPLETED",
    priority: "NORMAL",
    assigned_to: "u2",
    assigned_to_name: "Sarah Johnson",
    due_date: "2026-02-25",
    category: "SUBMITTALS",
    source_type: "SUBMITTAL",
    source_id: "sub1",
    completed_at: "2026-02-24T16:00:00Z",
    created_by_name: "John Smith",
    created_at: "2026-02-18T11:00:00Z",
    updated_at: "2026-02-24T16:00:00Z",
  },
  {
    id: "4",
    project_id: "p1",
    title: "Schedule pre-pour inspection for Level 2 slab",
    description: "Coordinate with structural engineer and city inspector for pre-pour.",
    status: "OPEN",
    priority: "HIGH",
    assigned_to: "u1",
    assigned_to_name: "John Smith",
    due_date: "2026-03-05",
    category: "INSPECTIONS",
    created_by_name: "Sarah Johnson",
    created_at: "2026-02-22T08:00:00Z",
    updated_at: "2026-02-22T08:00:00Z",
  },
  {
    id: "5",
    project_id: "p1",
    title: "Update project contact directory",
    description: "Add new subcontractor contacts and verify phone/email.",
    status: "OPEN",
    priority: "LOW",
    assigned_to: "u4",
    assigned_to_name: "Jane Doe",
    due_date: "2026-03-10",
    category: "ADMIN",
    created_by_name: "John Smith",
    created_at: "2026-02-20T14:00:00Z",
    updated_at: "2026-02-20T14:00:00Z",
  },
];

const KANBAN_COLUMNS = [
  { id: "OPEN", title: "To Do", color: "bg-blue-400" },
  { id: "IN_PROGRESS", title: "In Progress", color: "bg-yellow-400" },
  { id: "COMPLETED", title: "Done", color: "bg-green-400" },
];

export default function TasksPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [view, setView] = useState<"table" | "board">("table");
  const [sortKey, setSortKey] = useState("due_date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_TODOS;
  if (statusFilter) filtered = filtered.filter((t) => t.status === statusFilter);
  if (priorityFilter) filtered = filtered.filter((t) => t.priority === priorityFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (t) =>
        t.title.toLowerCase().includes(s) ||
        (t.category && t.category.toLowerCase().includes(s)) ||
        (t.assigned_to_name && t.assigned_to_name.toLowerCase().includes(s))
    );
  }

  const columns: Column<Todo>[] = [
    {
      key: "title",
      label: "Task",
      sortable: true,
      className: "max-w-sm",
      render: (row) => (
        <div>
          <span className="font-medium truncate block max-w-sm">{row.title}</span>
          {row.category && (
            <span className="text-xs text-gray-500">{row.category}</span>
          )}
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
      key: "priority",
      label: "Priority",
      sortable: true,
      render: (row) => (
        <span className={`text-sm ${PRIORITY_STYLES[row.priority] || ""}`}>
          {row.priority}
        </span>
      ),
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
        if (!row.due_date) return "\u2014";
        const due = new Date(row.due_date + "T00:00:00");
        const isOverdue = row.status !== "COMPLETED" && due < new Date();
        return (
          <span className={isOverdue ? "text-red-600 font-medium" : ""}>
            {due.toLocaleDateString()}
          </span>
        );
      },
    },
    {
      key: "source_type",
      label: "Source",
      render: (row) =>
        row.source_type ? (
          <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">
            {row.source_type}
          </span>
        ) : null,
    },
    {
      key: "updated_at",
      label: "Updated",
      sortable: true,
      render: (row) => new Date(row.updated_at).toLocaleDateString(),
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

  const hasData = MOCK_TODOS.length > 0;
  const openCount = MOCK_TODOS.filter((t) => t.status === "OPEN").length;
  const inProgressCount = MOCK_TODOS.filter((t) => t.status === "IN_PROGRESS").length;
  const completedCount = MOCK_TODOS.filter((t) => t.status === "COMPLETED").length;

  const kanbanColumns = KANBAN_COLUMNS.map((col) => ({
    ...col,
    items: filtered.filter((t) => t.status === col.id),
  }));

  return (
    <div>
      <PageHeader
        title="Tasks"
        subtitle="Manage and assign project tasks"
        action={
          <div className="flex items-center gap-3">
            {hasData && <ViewToggle view={view} onViewChange={setView} />}
            <button
              onClick={() => router.push(`/app/projects/${projectId}/todo/new`)}
              className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              New Task
            </button>
          </div>
        }
      />

      {hasData && (
        <div className="grid grid-cols-3 gap-4 mb-5">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">To Do</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">{openCount}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">In Progress</div>
            <div className="text-2xl font-bold text-yellow-600 mt-1">{inProgressCount}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Completed</div>
            <div className="text-2xl font-bold text-green-600 mt-1">{completedCount}</div>
          </div>
        </div>
      )}

      {hasData ? (
        <>
          <FilterBar
            searchPlaceholder="Search tasks..."
            searchValue={search}
            onSearchChange={setSearch}
            filters={[
              {
                key: "status",
                label: "All Statuses",
                value: statusFilter,
                onChange: setStatusFilter,
                options: [
                  { label: "Open", value: "OPEN" },
                  { label: "In Progress", value: "IN_PROGRESS" },
                  { label: "Completed", value: "COMPLETED" },
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

          {view === "table" ? (
            <DataTable
              columns={columns}
              data={filtered}
              sortKey={sortKey}
              sortOrder={sortOrder}
              onSort={handleSort}
              onRowClick={(row) => router.push(`/app/projects/${projectId}/todo/${row.id}`)}
              page={page}
              totalPages={1}
              total={filtered.length}
              onPageChange={setPage}
            />
          ) : (
            <KanbanBoard
              columns={kanbanColumns}
              getItemId={(item) => item.id}
              renderCard={(item) => (
                <div className="bg-white rounded-lg border border-gray-200 p-3 shadow-sm hover:shadow-md transition-shadow">
                  <p className="text-sm font-medium">{item.title}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className={`text-xs ${PRIORITY_STYLES[item.priority] || ""}`}>{item.priority}</span>
                    {item.due_date && (
                      <span className="text-[10px] text-gray-400">
                        {new Date(item.due_date + "T00:00:00").toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  {item.assigned_to_name && (
                    <p className="text-xs text-gray-500 mt-1">{item.assigned_to_name}</p>
                  )}
                </div>
              )}
            />
          )}
        </>
      ) : (
        <EmptyState
          icon={CheckSquare}
          title="No tasks yet"
          description="Create your first task to start managing project work."
          actionLabel="Create Task"
          onAction={() => router.push(`/app/projects/${projectId}/todo/new`)}
        />
      )}
    </div>
  );
}
