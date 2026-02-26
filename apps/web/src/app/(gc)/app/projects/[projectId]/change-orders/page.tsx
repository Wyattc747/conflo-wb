"use client";

import { Plus, FileText } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function ChangeOrdersPage() {
  return (
    <div>
      <PageHeader
        title="Change Orders"
        subtitle="Track and manage project change orders"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Change Order
          </button>
        }
      />
      <EmptyState
        icon={FileText}
        title="No change orders yet"
        description="Create your first change order to track project changes."
        actionLabel="Create Change Order"
        onAction={() => {}}
      />
    </div>
  );
}
