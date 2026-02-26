"use client";

import { Archive } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function SubCloseoutPage() {
  return (
    <div>
      <PageHeader title="Closeout" subtitle="Submit closeout documentation" />
      <EmptyState
        icon={Archive}
        title="Closeout not started"
        description="Closeout requirements will appear here when the project enters the Closeout phase."
      />
    </div>
  );
}
