"use client";

import { Plus, Package } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function BidPackagesPage() {
  return (
    <div>
      <PageHeader
        title="Bid Packages"
        subtitle="Create and manage bid packages for subcontractors"
        action={
          <button className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Bid Package
          </button>
        }
      />
      <EmptyState
        icon={Package}
        title="No bid packages yet"
        description="Create your first bid package to start collecting bids."
        actionLabel="Create Bid Package"
        onAction={() => {}}
      />
    </div>
  );
}
