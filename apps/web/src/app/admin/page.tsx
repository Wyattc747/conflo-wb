"use client";

import { useEffect, useState } from "react";
import { useAdmin } from "./layout";
import { Building2, Users, FolderKanban, DollarSign, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PlatformStats {
  total_organizations: number;
  total_users: number;
  total_projects: number;
  total_sub_companies: number;
  monthly_recurring_revenue: number;
  orgs_by_tier: Record<string, number>;
}

export default function AdminDashboard() {
  const { token } = useAdmin();
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    fetch(`${API_BASE}/api/admin/stats`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((d) => setStats(d.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="py-12 text-center">
        <Loader2 className="h-8 w-8 text-gray-400 animate-spin mx-auto" />
      </div>
    );
  }

  const cards = [
    { label: "Organizations", value: stats?.total_organizations || 0, icon: Building2, color: "bg-blue-500" },
    { label: "GC Users", value: stats?.total_users || 0, icon: Users, color: "bg-green-500" },
    { label: "Projects", value: stats?.total_projects || 0, icon: FolderKanban, color: "bg-purple-500" },
    { label: "MRR", value: `$${((stats?.monthly_recurring_revenue || 0) / 100).toLocaleString()}`, icon: DollarSign, color: "bg-yellow-500" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Platform Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.label} className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-center gap-3">
                <div className={`h-10 w-10 ${card.color} rounded-lg flex items-center justify-center`}>
                  <Icon className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">{card.label}</p>
                  <p className="text-xl font-bold text-gray-900">{card.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Tier breakdown */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Organizations by Tier</h2>
        <div className="space-y-3">
          {Object.entries(stats?.orgs_by_tier || {}).map(([tier, count]) => (
            <div key={tier} className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">{tier}</span>
              <div className="flex items-center gap-3">
                <div className="w-48 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${Math.min(100, (count / Math.max(1, stats?.total_organizations || 1)) * 100)}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-gray-900 w-8 text-right">{count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
