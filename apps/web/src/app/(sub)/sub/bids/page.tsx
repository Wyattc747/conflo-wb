"use client";

import { Gavel } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function SubBidsPage() {
  return (
    <div>
      <PageHeader title="Bids" subtitle="View and respond to bid invitations" />
      <EmptyState
        icon={Gavel}
        title="No active bids"
        description="Bid invitations will appear here when a GC sends you a bid package."
      />
    </div>
  );
}
