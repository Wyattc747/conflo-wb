"use client";

import { UserPlus } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function ProjectAssignmentsPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        title="Project Assignments"
        subtitle="Manage who has access to which projects"
      />
      <EmptyState
        icon={UserPlus}
        title="No assignments yet"
        description="Assign team members to projects to grant them access."
        actionLabel="Create Assignment"
        onAction={() => {}}
      />
    </div>
  );
}
