"use client";

import { createContext, useContext } from "react";

interface ProjectContextType {
  projectId: string;
  projectName: string;
  visibleTools: string[];
}

const ProjectContext = createContext<ProjectContextType | null>(null);

export function ProjectProvider({
  projectId,
  projectName,
  visibleTools,
  children,
}: {
  projectId: string;
  projectName: string;
  visibleTools: string[];
  children: React.ReactNode;
}) {
  return (
    <ProjectContext.Provider value={{ projectId, projectName, visibleTools }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (!context) throw new Error("useProject must be used within ProjectProvider");
  return context;
}
