"use client";

import { Plus, HelpCircle } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function RFIsPage() {
  return (
    <div>
      <PageHeader
        title="RFIs"
        subtitle="Manage requests for information"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New RFI
          </button>
        }
      />
      <EmptyState
        icon={HelpCircle}
        title="No RFIs yet"
        description="Create your first RFI to start tracking requests for information."
        actionLabel="Create RFI"
        onAction={() => {}}
      />
    </div>
  );
}
