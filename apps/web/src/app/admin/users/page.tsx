"use client";

import { useState } from "react";
import { useAdmin } from "../layout";
import { Search, Users, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UserResult {
  id: string;
  name: string;
  email: string;
  user_type: string;
  organization_name: string | null;
  status: string;
}

const TYPE_COLORS: Record<string, string> = {
  gc: "bg-blue-100 text-blue-700",
  sub: "bg-green-100 text-green-700",
  owner: "bg-purple-100 text-purple-700",
};

export default function UsersPage() {
  const { token } = useAdmin();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<UserResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!token || !query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/search?q=${encodeURIComponent(query)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setResults(data.data || []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">User Search</h1>

      <div className="flex gap-2 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search by email or name..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="py-8 text-center"><Loader2 className="h-6 w-6 text-gray-400 animate-spin mx-auto" /></div>
        ) : !searched ? (
          <div className="py-8 text-center">
            <Users className="h-8 w-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">Search for users by email or name</p>
          </div>
        ) : results.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-gray-500">No users found for &quot;{query}&quot;</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Email</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Type</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Organization</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {results.map((user) => (
                <tr key={`${user.user_type}-${user.id}`} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{user.name}</td>
                  <td className="px-4 py-3 text-gray-600">{user.email}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${TYPE_COLORS[user.user_type] || "bg-gray-100"}`}>
                      {user.user_type.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{user.organization_name || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium ${user.status === "ACTIVE" ? "text-green-600" : "text-gray-500"}`}>
                      {user.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
