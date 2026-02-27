"use client";

import { useEffect, useState } from "react";
import { useAdmin } from "../layout";
import { BarChart3, Activity, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TOOL_LABELS: Record<string, string> = {
  rfis: "RFIs",
  submittals: "Submittals",
  change_orders: "Change Orders",
  pay_apps: "Pay Applications",
  punch_list: "Punch List",
  daily_logs: "Daily Logs",
  meetings: "Meetings",
  todos: "To-Dos",
  drawings: "Drawings",
  documents: "Documents",
  bid_packages: "Bid Packages",
  inspections: "Inspections",
  schedule_tasks: "Schedule Tasks",
  procurement: "Procurement",
  transmittals: "Transmittals",
};

export default function MetricsPage() {
  const { token } = useAdmin();
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    // Use the benchmarks endpoint for tool usage (GC endpoint - admin can call via admin token indirectly, or we display static for now)
    // For a real implementation this would call an admin-specific metrics endpoint
    // For now show placeholder
    setLoading(false);
    setStats({
      rfis: 0, submittals: 0, change_orders: 0, pay_apps: 0,
      punch_list: 0, daily_logs: 0, meetings: 0, todos: 0,
      drawings: 0, documents: 0, bid_packages: 0, inspections: 0,
      schedule_tasks: 0, procurement: 0, transmittals: 0,
    });
  }, [token]);

  if (loading) {
    return <div className="py-12 text-center"><Loader2 className="h-8 w-8 text-gray-400 animate-spin mx-auto" /></div>;
  }

  const sortedTools = Object.entries(stats || {}).sort((a, b) => b[1] - a[1]);
  const maxCount = Math.max(1, ...sortedTools.map(([, c]) => c));

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Platform Metrics</h1>

      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <BarChart3 className="h-5 w-5" /> Tool Usage (All Organizations)
        </h2>
        <div className="space-y-3">
          {sortedTools.map(([tool, count]) => (
            <div key={tool} className="flex items-center gap-3">
              <span className="text-sm text-gray-700 w-36">{TOOL_LABELS[tool] || tool}</span>
              <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all"
                  style={{ width: `${(count / maxCount) * 100}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-gray-900 w-12 text-right">{count}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Activity className="h-5 w-5" /> Activity Timeline
        </h2>
        <p className="text-sm text-gray-500">
          Activity data will populate once events are being logged. Run the test seeder to create sample data.
        </p>
      </div>
    </div>
  );
}
