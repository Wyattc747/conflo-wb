"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { PayApp, PayAppCreateInput } from "@/types/pay-app";
import type { ListResponse } from "@/types/common";

export function usePayApps(
  portal: "gc" | "sub" | "owner",
  projectId: string,
  token: string | null,
  params?: { pay_app_type?: string; status?: string; page?: number; per_page?: number }
) {
  const queryParams = new URLSearchParams();
  if (params?.pay_app_type) queryParams.set("pay_app_type", params.pay_app_type);
  if (params?.status) queryParams.set("status", params.status);
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));

  return useQuery<ListResponse<PayApp>>({
    queryKey: ["pay-apps", portal, projectId, params],
    queryFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/pay-apps?${queryParams}`, token!),
    enabled: !!token,
  });
}

export function usePayApp(portal: "gc" | "sub" | "owner", projectId: string, payAppId: string, token: string | null) {
  return useQuery<{ data: PayApp }>({
    queryKey: ["pay-app", portal, projectId, payAppId],
    queryFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/pay-apps/${payAppId}`, token!),
    enabled: !!token && !!payAppId,
  });
}

export function useCreatePayApp(portal: "gc" | "sub", projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PayAppCreateInput) =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/pay-apps`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pay-apps"] });
    },
  });
}

export function useSubmitPayApp(portal: "gc" | "sub", projectId: string, payAppId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/pay-apps/${payAppId}/submit`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pay-apps"] });
      queryClient.invalidateQueries({ queryKey: ["pay-app"] });
    },
  });
}

export function useApprovePayApp(portal: "gc" | "owner", projectId: string, payAppId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notes?: string) =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/pay-apps/${payAppId}/approve`, token!, {
        method: "POST",
        body: JSON.stringify(notes ? { notes } : {}),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pay-apps"] });
      queryClient.invalidateQueries({ queryKey: ["pay-app"] });
    },
  });
}

export function useRejectPayApp(portal: "gc" | "owner", projectId: string, payAppId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notes?: string) =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/pay-apps/${payAppId}/reject`, token!, {
        method: "POST",
        body: JSON.stringify(notes ? { notes } : {}),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pay-apps"] });
      queryClient.invalidateQueries({ queryKey: ["pay-app"] });
    },
  });
}
