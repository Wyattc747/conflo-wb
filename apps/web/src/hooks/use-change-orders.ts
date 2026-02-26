"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { ChangeOrder, ChangeOrderCreateInput, ChangeOrderUpdateInput } from "@/types/change-order";
import type { ListResponse } from "@/types/common";

export function useChangeOrders(
  portal: "gc" | "sub" | "owner",
  projectId: string,
  token: string | null,
  params?: { status?: string; reason?: string; priority?: string; search?: string; sort?: string; order?: string; page?: number; per_page?: number }
) {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.set("status", params.status);
  if (params?.reason) queryParams.set("reason", params.reason);
  if (params?.priority) queryParams.set("priority", params.priority);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));

  return useQuery<ListResponse<ChangeOrder>>({
    queryKey: ["change-orders", portal, projectId, params],
    queryFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/change-orders?${queryParams}`, token!),
    enabled: !!token,
  });
}

export function useChangeOrder(portal: "gc" | "sub" | "owner", projectId: string, coId: string, token: string | null) {
  return useQuery<{ data: ChangeOrder }>({
    queryKey: ["change-order", portal, projectId, coId],
    queryFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/change-orders/${coId}`, token!),
    enabled: !!token && !!coId,
  });
}

export function useCreateChangeOrder(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ChangeOrderCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/change-orders`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["change-orders"] });
    },
  });
}

export function useUpdateChangeOrder(projectId: string, coId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ChangeOrderUpdateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/change-orders/${coId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["change-orders"] });
      queryClient.invalidateQueries({ queryKey: ["change-order"] });
    },
  });
}

export function useDeleteChangeOrder(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (coId: string) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/change-orders/${coId}`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["change-orders"] });
    },
  });
}

export function useSubmitToOwner(projectId: string, coId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/change-orders/${coId}/submit-to-owner`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["change-orders"] });
      queryClient.invalidateQueries({ queryKey: ["change-order"] });
    },
  });
}

export function useSubmitSubPricing(projectId: string, coId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { amount: number; description: string; schedule_impact_days: number }) =>
      fetchWithAuth(`/api/sub/projects/${projectId}/change-orders/${coId}/submit-pricing`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["change-orders"] });
      queryClient.invalidateQueries({ queryKey: ["change-order"] });
    },
  });
}

export function useOwnerCODecision(projectId: string, coId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { decision: "approve" | "reject"; notes?: string }) =>
      fetchWithAuth(`/api/owner/projects/${projectId}/change-orders/${coId}/${data.decision}`, token!, {
        method: "POST",
        body: JSON.stringify(data.notes ? { notes: data.notes } : {}),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["change-orders"] });
      queryClient.invalidateQueries({ queryKey: ["change-order"] });
    },
  });
}
