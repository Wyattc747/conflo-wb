"use client";

import { Wrench } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function SubPunchListPage() {
  return (
    <div>
      <PageHeader title="Punch List" subtitle="View and complete assigned punch items" />
      <EmptyState
        icon={Wrench}
        title="No punch list items yet"
        description="Punch items assigned to you will appear here."
      />
    </div>
  );
}
