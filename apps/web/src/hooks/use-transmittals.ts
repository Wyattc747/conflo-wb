"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { Transmittal, TransmittalCreateInput } from "@/types/transmittal";
import type { ListResponse } from "@/types/common";

export function useTransmittals(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    status?: string;
    purpose?: string;
    search?: string;
    sort?: string;
    order?: string;
  }
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.status) queryParams.set("status", params.status);
  if (params?.purpose) queryParams.set("purpose", params.purpose);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<Transmittal>>({
    queryKey: ["transmittals", projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/gc/projects/${projectId}/transmittals?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useTransmittal(
  projectId: string,
  transmittalId: string,
  token: string | null
) {
  return useQuery<{ data: Transmittal }>({
    queryKey: ["transmittal", projectId, transmittalId],
    queryFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/transmittals/${transmittalId}`, token!),
    enabled: !!token && !!transmittalId,
  });
}

export function useCreateTransmittal(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TransmittalCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/transmittals`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transmittals", projectId] });
    },
  });
}

export function useSendTransmittal(
  projectId: string,
  transmittalId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/transmittals/${transmittalId}/send`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transmittals", projectId] });
      queryClient.invalidateQueries({ queryKey: ["transmittal", projectId, transmittalId] });
    },
  });
}

export function useConfirmTransmittal(
  projectId: string,
  transmittalId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/transmittals/${transmittalId}/acknowledge`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transmittals", projectId] });
      queryClient.invalidateQueries({ queryKey: ["transmittal", projectId, transmittalId] });
    },
  });
}
