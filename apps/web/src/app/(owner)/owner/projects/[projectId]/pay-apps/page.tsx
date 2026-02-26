"use client";

import { Receipt } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function OwnerPayAppsPage() {
  return (
    <div>
      <PageHeader title="Pay Applications" subtitle="Review and approve payment applications" />
      <EmptyState
        icon={Receipt}
        title="No pay applications yet"
        description="Pay applications will appear here when submitted by the GC."
      />
    </div>
  );
}
