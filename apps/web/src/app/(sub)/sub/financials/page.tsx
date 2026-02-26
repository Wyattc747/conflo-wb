"use client";

import { DollarSign } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function SubFinancialsPage() {
  return (
    <div>
      <PageHeader title="Financials" subtitle="Track pay applications and change orders across projects" />
      <EmptyState
        icon={DollarSign}
        title="No financial data yet"
        description="Pay applications and change orders will appear here as they are created."
      />
    </div>
  );
}
