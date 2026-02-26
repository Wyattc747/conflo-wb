"use client";

import { Calendar } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function SubSchedulePage() {
  return (
    <div>
      <PageHeader title="Schedule" subtitle="View your scope in the project schedule" />
      <EmptyState
        icon={Calendar}
        title="No schedule items yet"
        description="Your scheduled tasks will appear here once the GC builds the project schedule."
      />
    </div>
  );
}
