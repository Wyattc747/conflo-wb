"use client";

import { Plus, PenTool } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function DrawingsPage() {
  return (
    <div>
      <PageHeader
        title="Drawings"
        subtitle="Manage project drawing sets and revisions"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Upload Drawings
          </button>
        }
      />
      <EmptyState
        icon={PenTool}
        title="No drawings yet"
        description="Upload your first drawing set to start managing project drawings."
        actionLabel="Upload Drawings"
        onAction={() => {}}
      />
    </div>
  );
}
