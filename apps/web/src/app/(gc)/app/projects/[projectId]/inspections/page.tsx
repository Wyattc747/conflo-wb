"use client";

import { Plus, ClipboardCheck } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function InspectionsPage() {
  return (
    <div>
      <PageHeader
        title="Inspections"
        subtitle="Schedule and conduct project inspections"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Inspection
          </button>
        }
      />
      <EmptyState
        icon={ClipboardCheck}
        title="No inspections yet"
        description="Schedule your first inspection to ensure quality standards."
        actionLabel="Schedule Inspection"
        onAction={() => {}}
      />
    </div>
  );
}
