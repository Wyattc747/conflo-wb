"use client";

import { Plus, CheckSquare } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function TasksPage() {
  return (
    <div>
      <PageHeader
        title="Tasks"
        subtitle="Manage and assign project tasks"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Task
          </button>
        }
      />
      <EmptyState
        icon={CheckSquare}
        title="No tasks yet"
        description="Create your first task to start managing project work."
        actionLabel="Create Task"
        onAction={() => {}}
      />
    </div>
  );
}
