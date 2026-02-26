"use client";

import { PenTool } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export default function SubDrawingsPage() {
  return (
    <div>
      <PageHeader title="Drawings" subtitle="View and download project drawings" />
      <EmptyState
        icon={PenTool}
        title="No drawings yet"
        description="Drawings will appear here when uploaded by the GC."
      />
    </div>
  );
}
