"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { PunchListItem, PunchListItemCreateInput } from "@/types/punch-list";
import type { ListResponse } from "@/types/common";

export function usePunchList(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    status?: string;
    priority?: string;
    category?: string;
    assigned_to_sub_id?: string;
    search?: string;
    sort?: string;
    order?: string;
  },
  portal: "gc" | "sub" | "owner" = "gc"
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.status) queryParams.set("status", params.status);
  if (params?.priority) queryParams.set("priority", params.priority);
  if (params?.category) queryParams.set("category", params.category);
  if (params?.assigned_to_sub_id) queryParams.set("assigned_to_sub_id", params.assigned_to_sub_id);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<PunchListItem>>({
    queryKey: ["punch-list", portal, projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/${portal}/projects/${projectId}/punch-list?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function usePunchItem(
  projectId: string,
  itemId: string,
  token: string | null,
  portal: "gc" | "sub" | "owner" = "gc"
) {
  return useQuery<{ data: PunchListItem }>({
    queryKey: ["punch-item", portal, projectId, itemId],
    queryFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/punch-list/${itemId}`, token!),
    enabled: !!token && !!itemId,
  });
}

export function useCreatePunchItem(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PunchListItemCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/punch-list`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["punch-list", "gc", projectId] });
    },
  });
}

export function useCompletePunchItem(
  projectId: string,
  itemId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { completion_notes?: string; after_photo_ids?: string[] }) =>
      fetchWithAuth(`/api/sub/projects/${projectId}/punch-list/${itemId}/complete`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["punch-list"] });
      queryClient.invalidateQueries({ queryKey: ["punch-item"] });
    },
  });
}

export function useVerifyPunchItem(
  projectId: string,
  itemId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { verification_notes?: string; verification_photo_ids?: string[] }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/punch-list/${itemId}/verify`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["punch-list", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["punch-item", "gc", projectId, itemId] });
    },
  });
}

export function useClosePunchItem(
  projectId: string,
  itemId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/punch-list/${itemId}/close`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["punch-list", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["punch-item", "gc", projectId, itemId] });
    },
  });
}
