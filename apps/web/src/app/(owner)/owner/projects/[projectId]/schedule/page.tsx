"use client";

import { Calendar } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function OwnerSchedulePage() {
  return (
    <div>
      <PageHeader title="Schedule" subtitle="View project schedule and milestones" />
      <EmptyState
        icon={Calendar}
        title="No schedule items yet"
        description="The project schedule will appear here once the GC adds tasks and milestones."
      />
    </div>
  );
}
