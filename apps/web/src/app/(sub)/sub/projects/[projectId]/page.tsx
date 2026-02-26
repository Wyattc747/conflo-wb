"use client";

import { FileText, Clock } from "lucide-react";
import { PhaseBadge } from "@/components/shared/PhaseBadge";
import { Card } from "@/components/shared/Card";

export default function SubProjectOverviewPage() {
  return (
    <div>
      {/* Project hero */}
      <Card className="mb-4">
        <div className="flex items-start gap-4">
          <div className="hidden sm:flex h-16 w-16 rounded-lg bg-gray-100 items-center justify-center flex-shrink-0">
            <FileText className="h-6 w-6 text-gray-300" />
          </div>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-lg font-bold text-gray-900">Tech Campus Expansion</h2>
              <PhaseBadge phase="ACTIVE" />
            </div>
            <p className="text-sm text-gray-500 mb-1">Apex Construction</p>
            <p className="text-xs text-gray-400">Trade: Electrical</p>
          </div>
        </div>
      </Card>

      {/* Quick stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">OPEN RFIS</p>
          <p className="text-2xl font-bold text-gray-400">--</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">SUBMITTALS</p>
          <p className="text-2xl font-bold text-gray-400">--</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">PUNCH ITEMS</p>
          <p className="text-2xl font-bold text-gray-400">--</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">PAY APPS</p>
          <p className="text-2xl font-bold text-gray-400">--</p>
        </Card>
      </div>

      {/* Recent activity */}
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-4">Recent Activity</h3>
        <div className="flex flex-col items-center py-6 text-center">
          <Clock className="h-8 w-8 text-gray-300 mb-2" />
          <p className="text-sm text-gray-500">Activity will appear here as the project progresses.</p>
        </div>
      </Card>
    </div>
  );
}
