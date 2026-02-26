"use client";

import { Plus, Calendar } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function SchedulePage() {
  return (
    <div>
      <PageHeader
        title="Schedule"
        subtitle="Manage project schedule and milestones"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add Task
          </button>
        }
      />
      <EmptyState
        icon={Calendar}
        title="No schedule items yet"
        description="Add your first task to start building the project schedule."
        actionLabel="Add Task"
        onAction={() => {}}
      />
    </div>
  );
}
