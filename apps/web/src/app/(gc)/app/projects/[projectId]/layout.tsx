"use client";

import { ProjectSidebar } from "@/components/gc/ProjectSidebar";
import { ProjectProvider } from "@/providers/ProjectProvider";
import { MobileBottomTabs } from "@/components/gc/MobileBottomTabs";
import { useProjectSidebarStore } from "@/stores/ui-store";

// Stub: will be fetched from API
const VISIBLE_TOOLS = [
  "daily_logs", "rfis", "submittals", "transmittals", "change_orders",
  "schedule", "drawings", "punch_list", "inspections", "budget",
  "pay_apps", "meetings", "todo", "procurement", "look_ahead",
  "closeout", "documents", "photos",
];

export default function ProjectLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { projectId: string };
}) {
  const { collapsed } = useProjectSidebarStore();
  const projectId = params.projectId;
  const projectName = "Tech Campus Expansion";

  return (
    <ProjectProvider projectId={projectId} projectName={projectName} visibleTools={VISIBLE_TOOLS}>
      <div className="flex">
        <ProjectSidebar
          projectId={projectId}
          projectName={projectName}
          visibleTools={VISIBLE_TOOLS}
        />
        <div
          className={`flex-1 p-6 min-h-[calc(100vh-56px)] transition-all pb-20 md:pb-6 ${
            collapsed ? "md:ml-10" : "md:ml-[180px]"
          }`}
        >
          {children}
        </div>
        <MobileBottomTabs projectId={projectId} />
      </div>
    </ProjectProvider>
  );
}
