"use client";

import { BookOpen } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function OwnerSubmittalsPage() {
  return (
    <div>
      <PageHeader title="Submittals" subtitle="View and respond to project submittals" />
      <EmptyState
        icon={BookOpen}
        title="No submittals yet"
        description="Submittals will appear here when routed to you for review."
      />
    </div>
  );
}
