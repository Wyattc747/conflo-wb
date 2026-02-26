"use client";

import { Plus, Users } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function ProjectDirectoryPage() {
  return (
    <div>
      <PageHeader
        title="Project Directory"
        subtitle="Manage team members and project contacts"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add Contact
          </button>
        }
      />
      <EmptyState
        icon={Users}
        title="No team members yet"
        description="Add your first team member to start building the project directory."
        actionLabel="Add Contact"
        onAction={() => {}}
      />
    </div>
  );
}
