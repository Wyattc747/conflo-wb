"use client";

import { Plus, Users } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function TeamManagementPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        title="Team Management"
        subtitle="Manage team members and invitations"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Invite Member
          </button>
        }
      />
      <EmptyState
        icon={Users}
        title="No team members yet"
        description="Invite team members to start collaborating on projects."
        actionLabel="Invite Member"
        onAction={() => {}}
      />
    </div>
  );
}
