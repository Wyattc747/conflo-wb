"use client";

import { Activity } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function ActivityLogPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        title="Activity Log"
        subtitle="View all activity across your organization"
      />
      <Card>
        <div className="flex flex-col items-center py-8 text-center">
          <Activity className="h-10 w-10 text-gray-300 mb-3" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">No activity yet</h3>
          <p className="text-sm text-gray-500">Organization activity will appear here as your team works on projects.</p>
        </div>
      </Card>
    </div>
  );
}
