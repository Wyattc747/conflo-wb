"use client";

import { Plus, Wrench } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function PunchListPage() {
  return (
    <div>
      <PageHeader
        title="Punch List"
        subtitle="Track and resolve punch list items"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Punch Item
          </button>
        }
      />
      <EmptyState
        icon={Wrench}
        title="No punch list items yet"
        description="Create your first punch item to start tracking deficiencies."
        actionLabel="Create Punch Item"
        onAction={() => {}}
      />
    </div>
  );
}
