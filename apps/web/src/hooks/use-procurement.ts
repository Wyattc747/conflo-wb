"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type {
  ProcurementItem,
  ProcurementCreateInput,
  ProcurementUpdateInput,
} from "@/types/procurement";
import type { ListResponse } from "@/types/common";

export function useProcurementItems(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    status?: string;
    category?: string;
    vendor?: string;
    search?: string;
    sort?: string;
    order?: string;
  }
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.status) queryParams.set("status", params.status);
  if (params?.category) queryParams.set("category", params.category);
  if (params?.vendor) queryParams.set("vendor", params.vendor);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<ProcurementItem>>({
    queryKey: ["procurement", projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/gc/projects/${projectId}/procurement?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useProcurementItem(
  projectId: string,
  itemId: string,
  token: string | null
) {
  return useQuery<{ data: ProcurementItem }>({
    queryKey: ["procurement-item", projectId, itemId],
    queryFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/procurement/${itemId}`, token!),
    enabled: !!token && !!itemId,
  });
}

export function useCreateProcurementItem(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProcurementCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/procurement`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["procurement", projectId] });
    },
  });
}

export function useUpdateProcurementItem(
  projectId: string,
  itemId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProcurementUpdateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/procurement/${itemId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["procurement", projectId] });
      queryClient.invalidateQueries({ queryKey: ["procurement-item", projectId, itemId] });
    },
  });
}

export function useDeleteProcurementItem(
  projectId: string,
  itemId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/procurement/${itemId}`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["procurement", projectId] });
    },
  });
}

export function useQuoteProcurement(
  projectId: string,
  itemId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/procurement/${itemId}/quote`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["procurement", projectId] });
      queryClient.invalidateQueries({ queryKey: ["procurement-item", projectId, itemId] });
    },
  });
}

export function useOrderProcurement(
  projectId: string,
  itemId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/procurement/${itemId}/order`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["procurement", projectId] });
      queryClient.invalidateQueries({ queryKey: ["procurement-item", projectId, itemId] });
    },
  });
}

export function useShipProcurement(
  projectId: string,
  itemId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/procurement/${itemId}/ship`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["procurement", projectId] });
      queryClient.invalidateQueries({ queryKey: ["procurement-item", projectId, itemId] });
    },
  });
}

export function useDeliverProcurement(
  projectId: string,
  itemId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/procurement/${itemId}/deliver`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["procurement", projectId] });
      queryClient.invalidateQueries({ queryKey: ["procurement-item", projectId, itemId] });
    },
  });
}

export function useInstallProcurement(
  projectId: string,
  itemId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/procurement/${itemId}/install`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["procurement", projectId] });
      queryClient.invalidateQueries({ queryKey: ["procurement-item", projectId, itemId] });
    },
  });
}
