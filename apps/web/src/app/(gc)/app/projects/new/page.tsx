"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

const PROJECT_TYPES = [
  "Commercial", "Institutional", "Healthcare", "Education",
  "Industrial", "Residential Multi-Family", "Mixed Use", "Other",
];

export default function NewProjectPage() {
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-4">
        <Link href="/app/projects" className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" />
          Back to Projects
        </Link>
      </div>
      <PageHeader title="New Project" subtitle="Create a new construction project" />

      <Card>
        <form className="space-y-5">
          {/* Project Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Name *</label>
            <input
              type="text"
              placeholder="e.g. Tech Campus Expansion"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none"
            />
          </div>

          {/* Project Number */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Number</label>
            <input
              type="text"
              placeholder="e.g. PRJ-001"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none"
            />
          </div>

          {/* Project Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Type</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none bg-white">
              <option value="">Select type...</option>
              {PROJECT_TYPES.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          {/* Address */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <input
              type="text"
              placeholder="Project address"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none"
            />
          </div>

          {/* Contract Value */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contract Value</label>
            <input
              type="text"
              placeholder="$0.00"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none"
            />
          </div>

          {/* Phase */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Starting Phase</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none bg-white">
              <option value="BIDDING">Bidding</option>
              <option value="BUYOUT">Buyout</option>
              <option value="ACTIVE">Active</option>
            </select>
          </div>

          {/* Dates */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Estimated Start</label>
              <input
                type="date"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Estimated End</label>
              <input
                type="date"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none"
              />
            </div>
          </div>

          {/* Submit */}
          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              className="bg-[#1B2A4A] text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-[#243558]"
            >
              Create Project
            </button>
            <Link href="/app/projects" className="text-sm text-gray-500 hover:text-gray-700">
              Cancel
            </Link>
          </div>
        </form>
      </Card>
    </div>
  );
}
