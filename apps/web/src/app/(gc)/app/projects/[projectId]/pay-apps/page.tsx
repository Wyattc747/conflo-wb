"use client";

import { Plus, Receipt } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function PayApplicationsPage() {
  return (
    <div>
      <PageHeader
        title="Pay Applications"
        subtitle="Manage payment applications and billing"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Pay App
          </button>
        }
      />
      <EmptyState
        icon={Receipt}
        title="No pay applications yet"
        description="Create your first pay application to start the billing process."
        actionLabel="Create Pay App"
        onAction={() => {}}
      />
    </div>
  );
}
