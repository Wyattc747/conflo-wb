"use client";

import { FileText } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function OwnerChangeOrdersPage() {
  return (
    <div>
      <PageHeader title="Change Orders" subtitle="Review and approve change orders" />
      <EmptyState
        icon={FileText}
        title="No change orders yet"
        description="Change orders will appear here when submitted by the GC for your approval."
      />
    </div>
  );
}
