"use client";

import { Eye } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function LookAheadPage() {
  return (
    <div>
      <PageHeader
        title="Look Ahead"
        subtitle="View upcoming milestones and deadlines"
      />
      <EmptyState
        icon={Eye}
        title="No upcoming items"
        description="Upcoming tasks, deadlines, and milestones will appear here as you add project data."
      />
    </div>
  );
}
