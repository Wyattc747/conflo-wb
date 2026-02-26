"use client";

import { Archive } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function CloseoutPage() {
  return (
    <div>
      <PageHeader
        title="Closeout"
        subtitle="Manage project closeout documentation"
      />
      <EmptyState
        icon={Archive}
        title="Closeout not started"
        description="Closeout documentation will be available when the project enters the Closeout phase."
      />
    </div>
  );
}
