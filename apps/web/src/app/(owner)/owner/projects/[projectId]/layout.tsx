"use client";

import { OwnerProjectTabs } from "@/components/owner/OwnerProjectTabs";
import { OwnerMobileBottomTabs } from "@/components/owner/OwnerMobileBottomTabs";

// Stub: will be fetched from API based on owner_portal_config
const VISIBLE_TOOLS = [
  "pay_apps", "change_orders", "schedule", "punch_list",
  "submittals", "rfis", "drawings", "closeout", "directory",
];

export default function OwnerProjectLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { projectId: string };
}) {
  return (
    <div>
      <OwnerProjectTabs projectId={params.projectId} visibleTools={VISIBLE_TOOLS} />
      <div className="p-6 pb-20 md:pb-6">{children}</div>
      <OwnerMobileBottomTabs projectId={params.projectId} />
    </div>
  );
}
