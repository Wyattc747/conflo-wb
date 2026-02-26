"use client";

import { Plus, BookOpen } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function SubmittalsPage() {
  return (
    <div>
      <PageHeader
        title="Submittals"
        subtitle="Track and manage project submittals"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Submittal
          </button>
        }
      />
      <EmptyState
        icon={BookOpen}
        title="No submittals yet"
        description="Create your first submittal to start the review process."
        actionLabel="Create Submittal"
        onAction={() => {}}
      />
    </div>
  );
}
