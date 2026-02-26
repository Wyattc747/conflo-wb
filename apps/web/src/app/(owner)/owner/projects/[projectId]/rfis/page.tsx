"use client";

import { HelpCircle } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function OwnerRFIsPage() {
  return (
    <div>
      <PageHeader title="RFIs" subtitle="View and respond to requests for information" />
      <EmptyState
        icon={HelpCircle}
        title="No RFIs yet"
        description="RFIs will appear here when assigned to you for response."
      />
    </div>
  );
}
