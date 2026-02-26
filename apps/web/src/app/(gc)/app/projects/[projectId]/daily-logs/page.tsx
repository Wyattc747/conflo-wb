"use client";

import { Plus, ClipboardList } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function DailyLogsPage() {
  return (
    <div>
      <PageHeader
        title="Daily Logs"
        subtitle="Track daily project activity and conditions"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Daily Log
          </button>
        }
      />
      <EmptyState
        icon={ClipboardList}
        title="No daily logs yet"
        description="Create your first daily log to start tracking project activity."
        actionLabel="Create Daily Log"
        onAction={() => {}}
      />
    </div>
  );
}
