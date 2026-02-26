"use client";

import { Card } from "@/components/shared/Card";
import { Clock, Gavel, DollarSign, Wrench } from "lucide-react";

export default function SubDashboardPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500">Welcome back</p>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Gavel className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Active Bids</p>
              <p className="text-xl font-bold text-gray-900">--</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-green-100 flex items-center justify-center">
              <DollarSign className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Pay Apps</p>
              <p className="text-xl font-bold text-gray-900">--</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-red-100 flex items-center justify-center">
              <Wrench className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Punch Items</p>
              <p className="text-xl font-bold text-gray-900">--</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-yellow-100 flex items-center justify-center">
              <Clock className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Due This Week</p>
              <p className="text-xl font-bold text-gray-900">--</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent activity */}
      <Card>
        <h3 className="text-base font-semibold text-gray-900 mb-4">Recent Activity</h3>
        <div className="flex flex-col items-center py-6 text-center">
          <Clock className="h-8 w-8 text-gray-300 mb-2" />
          <p className="text-sm text-gray-500">Activity will appear here as you work on projects.</p>
        </div>
      </Card>
    </div>
  );
}
