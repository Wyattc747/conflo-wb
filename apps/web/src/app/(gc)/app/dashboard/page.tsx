"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { StatusBadge } from "@/components/shared/StatusBadge";

function StatCell({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="text-center py-1.5 sm:py-2">
      <p className="text-[10px] sm:text-xs uppercase tracking-wider text-gray-500 mb-0.5 sm:mb-1">{label}</p>
      <p className={`text-lg sm:text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

function FinancialCell({
  label,
  value,
  color,
  subtext,
}: {
  label: string;
  value: string;
  color: string;
  subtext?: string;
}) {
  return (
    <div>
      <p className="text-[10px] sm:text-xs uppercase tracking-wider text-gray-500 mb-0.5 sm:mb-1">{label}</p>
      <p className={`text-lg sm:text-2xl font-bold ${color}`}>{value}</p>
      {subtext && <p className="text-[10px] sm:text-xs text-gray-500 mt-0.5">{subtext}</p>}
    </div>
  );
}

function ProjectRow({
  name,
  address,
  actions,
  status,
}: {
  name: string;
  address: string;
  actions: number;
  status: string;
}) {
  return (
    <tr className="border-t border-gray-100">
      <td className="py-3 pr-3">
        <p className="text-sm font-medium text-gray-900 truncate max-w-[180px]">{name}</p>
      </td>
      <td className="py-3 pr-3">
        <p className="text-sm text-gray-500 truncate max-w-[240px]">{address}</p>
      </td>
      <td className="py-3 text-center">
        <span className="text-sm font-medium text-gray-900">{actions}</span>
      </td>
      <td className="py-3 text-right">
        <StatusBadge status={status} />
      </td>
    </tr>
  );
}

export default function DashboardPage() {
  return (
    <div className="p-3 sm:p-6 max-w-7xl mx-auto">
      {/* Page header */}
      <div className="mb-4 sm:mb-6">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-xs sm:text-sm text-gray-500">Welcome back, Marcus</p>
      </div>

      {/* Project Health */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-5 mb-3 sm:mb-4">
        <h2 className="text-sm sm:text-base font-semibold text-gray-900 mb-3 sm:mb-4">Project Health</h2>
        <div className="grid grid-cols-3 divide-x divide-gray-200">
          <StatCell label="ON TRACK" value={1} color="text-green-500" />
          <StatCell label="AT RISK" value={0} color="text-gray-900" />
          <StatCell label="BEHIND" value={0} color="text-gray-900" />
        </div>
      </div>

      {/* Action Items */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-5 mb-3 sm:mb-4">
        <h2 className="text-sm sm:text-base font-semibold text-gray-900 mb-3 sm:mb-4">Action Items</h2>
        <div className="grid grid-cols-3 md:grid-cols-6 divide-x divide-gray-200">
          <StatCell label="RFIS" value={12} color="text-accent" />
          <StatCell label="SUBMITTALS" value={8} color="text-gray-900" />
          <StatCell label="TRANSMITTALS" value={5} color="text-accent" />
          <StatCell label="PUNCH" value={23} color="text-red-500" />
          <StatCell label="TASKS" value={7} color="text-yellow-500" />
          <StatCell label="MEETINGS" value={4} color="text-gray-900" />
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-3 sm:gap-4">
        {/* Active Projects */}
        <div className="lg:col-span-3 bg-white rounded-lg border border-gray-200 p-4 sm:p-5 overflow-x-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Active Projects</h2>
            <Link
              href="/app/projects"
              className="text-sm text-accent hover:underline flex items-center gap-1"
            >
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <table className="w-full">
            <thead>
              <tr className="text-xs uppercase tracking-wider text-gray-500">
                <th className="text-left pb-2 font-medium">Project</th>
                <th className="text-left pb-2 font-medium hidden md:table-cell">Address</th>
                <th className="text-center pb-2 font-medium">Actions</th>
                <th className="text-right pb-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="text-sm text-gray-900">
              <ProjectRow
                name="Tech Campus Expansion"
                address="1000 Innovation Way, Palo Alto, CA 94301"
                actions={15}
                status="Behind"
              />
              <ProjectRow
                name="555 Market Street Tower"
                address="555 Market Street, San Francisco, CA 94105"
                actions={8}
                status="At Risk"
              />
            </tbody>
          </table>
        </div>

        {/* Financial Summary */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-4 sm:p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Financial Summary</h2>
            <Link
              href="/app/projects"
              className="text-sm text-accent hover:underline flex items-center gap-1"
            >
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <FinancialCell label="CONTRACT" value="$12,450,000" color="text-gray-900" />
            <FinancialCell label="BILLED" value="$8,234,500" color="text-accent" />
            <FinancialCell label="OUTSTANDING" value="$1,250,000" color="text-red-500" />
            <FinancialCell
              label="CHANGES"
              value="$385,000"
              subtext="12 pending"
              color="text-amber-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
