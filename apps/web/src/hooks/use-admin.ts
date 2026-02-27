import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function adminFetch(path: string, token: string | null, options?: RequestInit) {
  if (!token) throw new Error("No admin token");
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// Platform stats
export function useAdminStats(token: string | null) {
  return useQuery({
    queryKey: ["admin", "stats"],
    queryFn: () => adminFetch("/api/admin/stats", token),
    enabled: !!token,
  });
}

// Organizations list
export function useAdminOrganizations(
  token: string | null,
  params: { page?: number; per_page?: number; search?: string } = {}
) {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.per_page) searchParams.set("per_page", String(params.per_page));
  if (params.search) searchParams.set("search", params.search);
  const qs = searchParams.toString();

  return useQuery({
    queryKey: ["admin", "organizations", params],
    queryFn: () => adminFetch(`/api/admin/organizations${qs ? `?${qs}` : ""}`, token),
    enabled: !!token,
  });
}

// Organization detail
export function useAdminOrgDetail(token: string | null, orgId: string | null) {
  return useQuery({
    queryKey: ["admin", "organizations", orgId],
    queryFn: () => adminFetch(`/api/admin/organizations/${orgId}`, token),
    enabled: !!token && !!orgId,
  });
}

// User search
export function useAdminUserSearch(token: string | null, query: string) {
  return useQuery({
    queryKey: ["admin", "users", "search", query],
    queryFn: () => adminFetch(`/api/admin/users/search?q=${encodeURIComponent(query)}`, token),
    enabled: !!token && query.length >= 2,
  });
}

// Impersonation
export function useAdminImpersonate(token: string | null) {
  return useMutation({
    mutationFn: (data: { user_id: string; user_type: string }) =>
      adminFetch("/api/admin/impersonate", token, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  });
}
