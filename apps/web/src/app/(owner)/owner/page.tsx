"use client";

import Link from "next/link";
import { FolderOpen } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { PhaseBadge } from "@/components/shared/PhaseBadge";
import { Card } from "@/components/shared/Card";

const MOCK_PROJECTS = [
  {
    id: "1",
    name: "Tech Campus Expansion",
    gcCompany: "Apex Construction",
    address: "1000 Innovation Way, Palo Alto, CA 94301",
    phase: "ACTIVE",
    contractValue: "$8,500,000",
  },
];

export default function OwnerProjectsPage() {
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <PageHeader title="My Projects" subtitle="Projects shared with you" />

      {MOCK_PROJECTS.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {MOCK_PROJECTS.map((project) => (
            <Link key={project.id} href={`/owner/projects/${project.id}`}>
              <Card className="hover:border-yellow-300 transition-colors cursor-pointer">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-base font-semibold text-gray-900">{project.name}</h3>
                  <PhaseBadge phase={project.phase} />
                </div>
                <p className="text-sm text-gray-500 mb-1">{project.gcCompany}</p>
                <p className="text-xs text-gray-400 mb-3">{project.address}</p>
                <p className="text-sm font-medium text-gray-700">{project.contractValue}</p>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <FolderOpen className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">No projects yet</h3>
          <p className="text-sm text-gray-500">Projects will appear here when a GC shares them with you.</p>
        </Card>
      )}
    </div>
  );
}
