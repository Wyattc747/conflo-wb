"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, CheckSquare, CheckCircle } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { FilterBar } from "@/components/shared/FilterBar";
import { StatusBadge } from "@/components/shared/StatusBadge";
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
    title: "Submit steel shop drawing package",
    description: "Complete and submit shop drawings for structural steel.",
    status: "IN_PROGRESS",
    priority: "HIGH",
    assigned_to: "sub_u1",
    assigned_to_name: "Tom Wilson",
    due_date: "2026-03-05",
    category: "SUBMITTALS",
    created_by_name: "John Smith",
    created_at: "2026-02-18T10:00:00Z",
    updated_at: "2026-02-22T14:00:00Z",
  },
  {
    id: "2",
    project_id: "p1",
    title: "Update insurance certificate",
    description: "Renew and submit updated COI.",
    status: "OPEN",
    priority: "NORMAL",
    assigned_to: "sub_u1",
    assigned_to_name: "Tom Wilson",
    due_date: "2026-03-15",
    category: "ADMIN",
    created_by_name: "Tom Wilson",
    created_at: "2026-02-20T08:00:00Z",
    updated_at: "2026-02-20T08:00:00Z",
  },
  {
    id: "3",
    project_id: "p1",
    title: "Complete punch list items - Level 1",
    description: "Address all open punch items on Level 1.",
    status: "COMPLETED",
    priority: "HIGH",
    assigned_to: "sub_u2",
    assigned_to_name: "Sarah Kim",
    due_date: "2026-02-25",
    category: "PUNCH_LIST",
    completed_at: "2026-02-24T16:00:00Z",
    created_by_name: "John Smith",
    created_at: "2026-02-15T11:00:00Z",
    updated_at: "2026-02-24T16:00:00Z",
  },
];

export default function SubTodosPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState("due_date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  let filtered = MOCK_TODOS;
  if (statusFilter) filtered = filtered.filter((t) => t.status === statusFilter);
  if (search) {
    const s = search.toLowerCase();
    filtered = filtered.filter(
      (t) => t.title.toLowerCase().includes(s)
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
          {row.category && <span className="text-xs text-gray-500">{row.category}</span>}
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
        <span className={`text-sm ${PRIORITY_STYLES[row.priority] || ""}`}>{row.priority}</span>
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
      key: "actions",
      label: "",
      className: "w-28",
      render: (row) =>
        row.status === "IN_PROGRESS" ? (
          <button
            onClick={(e) => { e.stopPropagation(); console.log("complete", row.id); }}
            className="bg-green-600 text-white px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-green-700 flex items-center gap-1"
          >
            <CheckCircle className="h-3.5 w-3.5" />
            Complete
          </button>
        ) : null,
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

  return (
    <div>
      <PageHeader
        title="Tasks"
        subtitle="Manage your project tasks"
        action={
          <button
            onClick={() => router.push(`/sub/projects/${projectId}/todos/new`)}
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Task
          </button>
        }
      />

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
          icon={CheckSquare}
          title="No tasks yet"
          description="Create a task or wait for tasks to be assigned to you."
          actionLabel="Create Task"
          onAction={() => router.push(`/sub/projects/${projectId}/todos/new`)}
        />
      )}
    </div>
  );
}
