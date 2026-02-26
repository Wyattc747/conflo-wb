"use client";

import { Users } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function OwnerDirectoryPage() {
  return (
    <div>
      <PageHeader title="Directory" subtitle="View GC team and project contacts" />
      <EmptyState
        icon={Users}
        title="No team members yet"
        description="The project directory will appear here once team members are assigned."
      />
    </div>
  );
}
