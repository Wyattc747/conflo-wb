"use client";

import { Wrench } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function OwnerPunchListPage() {
  return (
    <div>
      <PageHeader title="Punch List" subtitle="View and track punch list items" />
      <EmptyState
        icon={Wrench}
        title="No punch list items yet"
        description="Punch list items will appear here as they are created by the project team."
      />
    </div>
  );
}
