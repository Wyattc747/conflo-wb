"use client";

import { Plus, ShoppingCart } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function ProcurementPage() {
  return (
    <div>
      <PageHeader
        title="Procurement"
        subtitle="Track material orders and deliveries"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Item
          </button>
        }
      />
      <EmptyState
        icon={ShoppingCart}
        title="No procurement items yet"
        description="Add your first procurement item to start tracking orders."
        actionLabel="Add Item"
        onAction={() => {}}
      />
    </div>
  );
}
