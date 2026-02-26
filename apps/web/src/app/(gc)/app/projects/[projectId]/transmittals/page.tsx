"use client";

import { Plus, Send } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function TransmittalsPage() {
  return (
    <div>
      <PageHeader
        title="Transmittals"
        subtitle="Send and track document transmittals"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Transmittal
          </button>
        }
      />
      <EmptyState
        icon={Send}
        title="No transmittals yet"
        description="Create your first transmittal to send documents."
        actionLabel="Create Transmittal"
        onAction={() => {}}
      />
    </div>
  );
}
