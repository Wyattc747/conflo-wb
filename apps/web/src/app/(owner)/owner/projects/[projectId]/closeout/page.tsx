"use client";

import { Archive } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function OwnerCloseoutPage() {
  return (
    <div>
      <PageHeader title="Closeout" subtitle="Receive project closeout documentation" />
      <EmptyState
        icon={Archive}
        title="Closeout not started"
        description="Closeout documentation will be delivered here when the project reaches the Closeout phase."
      />
    </div>
  );
}
