"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { RFI, RFICreateInput, RFIUpdateInput } from "@/types/rfi";
import type { ListResponse } from "@/types/common";

export function useRFIs(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    status?: string;
    priority?: string;
    assigned_to?: string;
    search?: string;
    sort?: string;
    order?: string;
  },
  portal: "gc" | "sub" = "gc"
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.status) queryParams.set("status", params.status);
  if (params?.priority) queryParams.set("priority", params.priority);
  if (params?.assigned_to) queryParams.set("assigned_to", params.assigned_to);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<RFI>>({
    queryKey: ["rfis", portal, projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/${portal}/projects/${projectId}/rfis?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useRFI(
  projectId: string,
  rfiId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  return useQuery<{ data: RFI }>({
    queryKey: ["rfi", portal, projectId, rfiId],
    queryFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/rfis/${rfiId}`, token!),
    enabled: !!token && !!rfiId,
  });
}

export function useCreateRFI(
  projectId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: RFICreateInput) =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/rfis`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rfis", portal, projectId] });
    },
  });
}

export function useUpdateRFI(projectId: string, rfiId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: RFIUpdateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/rfis/${rfiId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rfis", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["rfi", "gc", projectId, rfiId] });
    },
  });
}

export function useRespondRFI(
  projectId: string,
  rfiId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (response: string) =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/rfis/${rfiId}/respond`, token!, {
        method: "POST",
        body: JSON.stringify({ response }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rfis", portal, projectId] });
      queryClient.invalidateQueries({ queryKey: ["rfi", portal, projectId, rfiId] });
    },
  });
}

export function useCloseRFI(projectId: string, rfiId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/rfis/${rfiId}/close`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rfis", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["rfi", "gc", projectId, rfiId] });
    },
  });
}

export function useReopenRFI(projectId: string, rfiId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/rfis/${rfiId}/reopen`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rfis", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["rfi", "gc", projectId, rfiId] });
    },
  });
}
