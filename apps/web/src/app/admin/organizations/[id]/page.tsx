"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAdmin } from "../../layout";
import { ArrowLeft, Building2, Users, FolderKanban, UserCheck, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface OrgDetail {
  id: string;
  name: string;
  subscription_tier: string | null;
  subscription_status: string | null;
  phone: string | null;
  timezone: string | null;
  created_at: string | null;
  users: Array<{ id: string; name: string; email: string; permission_level: string; status: string }>;
  projects: Array<{ id: string; name: string; phase: string; contract_value: number | null }>;
}

export default function OrgDetailPage() {
  const { token } = useAdmin();
  const params = useParams();
  const router = useRouter();
  const [org, setOrg] = useState<OrgDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [impersonating, setImpersonating] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !params.id) return;
    fetch(`${API_BASE}/api/admin/organizations/${params.id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((d) => setOrg(d.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [token, params.id]);

  const handleImpersonate = async (userId: string, userType: string) => {
    if (!token) return;
    setImpersonating(userId);
    try {
      const res = await fetch(`${API_BASE}/api/admin/impersonate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ user_id: userId, user_type: userType }),
      });
      const data = await res.json();
      if (data.data?.token) {
        // Open in new tab with impersonation token
        window.open(`/app/dashboard?_impersonate=${data.data.token}`, "_blank");
      }
    } catch {
      // Error handled silently
    } finally {
      setImpersonating(null);
    }
  };

  if (loading) {
    return <div className="py-12 text-center"><Loader2 className="h-8 w-8 text-gray-400 animate-spin mx-auto" /></div>;
  }

  if (!org) {
    return <div className="py-12 text-center text-gray-500">Organization not found</div>;
  }

  return (
    <div>
      <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft className="h-4 w-4" /> Back
      </button>

      <div className="flex items-center gap-3 mb-6">
        <div className="h-12 w-12 bg-blue-100 rounded-xl flex items-center justify-center">
          <Building2 className="h-6 w-6 text-blue-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{org.name}</h1>
          <p className="text-sm text-gray-500">{org.subscription_tier} — {org.subscription_status}</p>
        </div>
      </div>

      {/* Users */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Users className="h-5 w-5" /> Users ({org.users?.length || 0})
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 font-medium text-gray-500">Name</th>
              <th className="text-left py-2 font-medium text-gray-500">Email</th>
              <th className="text-left py-2 font-medium text-gray-500">Role</th>
              <th className="text-left py-2 font-medium text-gray-500">Status</th>
              <th className="text-right py-2 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {(org.users || []).map((user) => (
              <tr key={user.id}>
                <td className="py-2 font-medium text-gray-900">{user.name}</td>
                <td className="py-2 text-gray-600">{user.email}</td>
                <td className="py-2"><span className="px-2 py-0.5 text-xs bg-gray-100 rounded-full">{user.permission_level}</span></td>
                <td className="py-2"><span className={`text-xs font-medium ${user.status === "ACTIVE" ? "text-green-600" : "text-gray-500"}`}>{user.status}</span></td>
                <td className="py-2 text-right">
                  <button
                    onClick={() => handleImpersonate(user.id, "gc")}
                    disabled={impersonating === user.id}
                    className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium"
                  >
                    {impersonating === user.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <UserCheck className="h-3 w-3" />}
                    Impersonate
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Projects */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FolderKanban className="h-5 w-5" /> Projects ({org.projects?.length || 0})
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 font-medium text-gray-500">Name</th>
              <th className="text-left py-2 font-medium text-gray-500">Phase</th>
              <th className="text-right py-2 font-medium text-gray-500">Contract Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {(org.projects || []).map((proj) => (
              <tr key={proj.id}>
                <td className="py-2 font-medium text-gray-900">{proj.name}</td>
                <td className="py-2"><span className="px-2 py-0.5 text-xs bg-gray-100 rounded-full">{proj.phase}</span></td>
                <td className="py-2 text-right text-gray-600">
                  {proj.contract_value ? `$${Number(proj.contract_value).toLocaleString()}` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
