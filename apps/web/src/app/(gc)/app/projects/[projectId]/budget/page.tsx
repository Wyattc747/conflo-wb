"use client";

import { Plus, DollarSign } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function BudgetPage() {
  return (
    <div>
      <PageHeader
        title="Budget"
        subtitle="Track project costs and budget"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add Line Item
          </button>
        }
      />
      <EmptyState
        icon={DollarSign}
        title="No budget items yet"
        description="Add your first budget line item to start tracking project costs."
        actionLabel="Add Line Item"
        onAction={() => {}}
      />
    </div>
  );
}
