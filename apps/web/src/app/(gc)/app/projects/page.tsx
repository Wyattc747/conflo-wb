"use client";

import Link from "next/link";
import { Plus, FolderOpen } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { PhaseBadge } from "@/components/shared/PhaseBadge";
import { StatusBadge } from "@/components/shared/StatusBadge";

const MOCK_PROJECTS = [
  {
    id: "1",
    name: "Tech Campus Expansion",
    number: "PRJ-001",
    address: "1000 Innovation Way, Palo Alto, CA 94301",
    phase: "ACTIVE",
    status: "Behind",
    contractValue: "$8,500,000",
  },
  {
    id: "2",
    name: "555 Market Street Tower",
    number: "PRJ-002",
    address: "555 Market Street, San Francisco, CA 94105",
    phase: "ACTIVE",
    status: "At Risk",
    contractValue: "$12,450,000",
  },
];

export default function ProjectsPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        title="Projects"
        subtitle="Manage all your construction projects"
        action={
          <Link
            href="/app/projects/new"
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Project
          </Link>
        }
      />

      {MOCK_PROJECTS.length > 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-3 text-xs uppercase tracking-wider text-gray-500 font-medium">
                  Project
                </th>
                <th className="text-left px-4 py-3 text-xs uppercase tracking-wider text-gray-500 font-medium hidden md:table-cell">
                  Address
                </th>
                <th className="text-center px-4 py-3 text-xs uppercase tracking-wider text-gray-500 font-medium">
                  Phase
                </th>
                <th className="text-center px-4 py-3 text-xs uppercase tracking-wider text-gray-500 font-medium hidden sm:table-cell">
                  Status
                </th>
                <th className="text-right px-4 py-3 text-xs uppercase tracking-wider text-gray-500 font-medium hidden lg:table-cell">
                  Contract Value
                </th>
              </tr>
            </thead>
            <tbody>
              {MOCK_PROJECTS.map((project) => (
                <tr key={project.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link
                      href={`/app/projects/${project.id}`}
                      className="text-sm font-medium text-gray-900 hover:text-accent"
                    >
                      {project.name}
                    </Link>
                    <p className="text-xs text-gray-500">{project.number}</p>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <p className="text-sm text-gray-500 truncate max-w-[280px]">{project.address}</p>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <PhaseBadge phase={project.phase} />
                  </td>
                  <td className="px-4 py-3 text-center hidden sm:table-cell">
                    <StatusBadge status={project.status} />
                  </td>
                  <td className="px-4 py-3 text-right hidden lg:table-cell">
                    <span className="text-sm font-medium text-gray-900">{project.contractValue}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <FolderOpen className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">No projects yet</h3>
          <p className="text-sm text-gray-500 mb-4">Create your first project to get started.</p>
          <Link
            href="/app/projects/new"
            className="bg-[#1B2A4A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#243558] inline-flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Project
          </Link>
        </div>
      )}
    </div>
  );
}
