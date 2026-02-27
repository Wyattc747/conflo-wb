"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAdmin } from "../layout";
import { Search, Building2, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface OrgListItem {
  id: string;
  name: string;
  subscription_tier: string | null;
  subscription_status: string | null;
  user_count: number;
  project_count: number;
  created_at: string | null;
}

const TIER_COLORS: Record<string, string> = {
  STARTER: "bg-gray-100 text-gray-700",
  PROFESSIONAL: "bg-blue-100 text-blue-700",
  SCALE: "bg-purple-100 text-purple-700",
  ENTERPRISE: "bg-yellow-100 text-yellow-700",
};

export default function OrganizationsPage() {
  const { token } = useAdmin();
  const router = useRouter();
  const [orgs, setOrgs] = useState<OrgListItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), per_page: "25" });
    if (search) params.set("search", search);

    fetch(`${API_BASE}/api/admin/organizations?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((d) => {
        setOrgs(d.data || []);
        setTotal(d.meta?.total || 0);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [token, page, search]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Organizations</h1>
        <span className="text-sm text-gray-500">{total} total</span>
      </div>

      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search organizations..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="py-8 text-center">
            <Loader2 className="h-6 w-6 text-gray-400 animate-spin mx-auto" />
          </div>
        ) : orgs.length === 0 ? (
          <div className="py-8 text-center">
            <Building2 className="h-8 w-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">No organizations found</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Tier</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Users</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Projects</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {orgs.map((org) => (
                <tr
                  key={org.id}
                  onClick={() => router.push(`/admin/organizations/${org.id}`)}
                  className="hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-4 py-3 font-medium text-gray-900">{org.name}</td>
                  <td className="px-4 py-3">
                    {org.subscription_tier && (
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${TIER_COLORS[org.subscription_tier] || "bg-gray-100 text-gray-600"}`}>
                        {org.subscription_tier}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium ${org.subscription_status === "ACTIVE" ? "text-green-600" : "text-gray-500"}`}>
                      {org.subscription_status || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600">{org.user_count}</td>
                  <td className="px-4 py-3 text-right text-gray-600">{org.project_count}</td>
                  <td className="px-4 py-3 text-right text-gray-500">
                    {org.created_at ? new Date(org.created_at).toLocaleDateString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {total > 25 && (
        <div className="flex justify-between items-center mt-4">
          <p className="text-sm text-gray-500">Page {page} of {Math.ceil(total / 25)}</p>
          <div className="flex gap-2">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1.5 text-sm rounded border border-gray-300 disabled:opacity-50">Previous</button>
            <button disabled={page >= Math.ceil(total / 25)} onClick={() => setPage(p => p + 1)} className="px-3 py-1.5 text-sm rounded border border-gray-300 disabled:opacity-50">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
