"use client";

import Link from "next/link";
import { FolderOpen } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { PhaseBadge } from "@/components/shared/PhaseBadge";
import { Card } from "@/components/shared/Card";

const MOCK_PROJECTS_BY_GC = [
  {
    gcName: "Apex Construction",
    projects: [
      {
        id: "1",
        name: "Tech Campus Expansion",
        address: "1000 Innovation Way, Palo Alto, CA 94301",
        phase: "ACTIVE",
        trade: "Electrical",
      },
    ],
  },
];

export default function SubProjectsPage() {
  return (
    <div>
      <PageHeader title="Projects" subtitle="Your active projects grouped by GC" />

      {MOCK_PROJECTS_BY_GC.length > 0 ? (
        <div className="space-y-6">
          {MOCK_PROJECTS_BY_GC.map((gc) => (
            <div key={gc.gcName}>
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">
                {gc.gcName}
              </h3>
              <div className="space-y-2">
                {gc.projects.map((project) => (
                  <Link key={project.id} href={`/sub/projects/${project.id}`}>
                    <Card className="hover:border-yellow-300 transition-colors cursor-pointer">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-semibold text-gray-900">{project.name}</h4>
                          <p className="text-xs text-gray-500">{project.address}</p>
                          <p className="text-xs text-gray-400 mt-1">Trade: {project.trade}</p>
                        </div>
                        <PhaseBadge phase={project.phase} />
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <FolderOpen className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">No projects yet</h3>
          <p className="text-sm text-gray-500">
            Projects will appear here when a GC invites you.
          </p>
        </Card>
      )}
    </div>
  );
}
