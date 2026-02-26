"use client";

import { Plus, Users2 } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function MeetingsPage() {
  return (
    <div>
      <PageHeader
        title="Meetings"
        subtitle="Schedule meetings and track minutes"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Meeting
          </button>
        }
      />
      <EmptyState
        icon={Users2}
        title="No meetings yet"
        description="Schedule your first meeting to start tracking agendas and minutes."
        actionLabel="Schedule Meeting"
        onAction={() => {}}
      />
    </div>
  );
}
