"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { Submittal, SubmittalCreateInput } from "@/types/submittal";
import type { ListResponse } from "@/types/common";

export function useSubmittals(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    status?: string;
    submittal_type?: string;
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
  if (params?.submittal_type) queryParams.set("submittal_type", params.submittal_type);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<Submittal>>({
    queryKey: ["submittals", portal, projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/${portal}/projects/${projectId}/submittals?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useSubmittal(
  projectId: string,
  submittalId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  return useQuery<{ data: Submittal }>({
    queryKey: ["submittal", portal, projectId, submittalId],
    queryFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/submittals/${submittalId}`, token!),
    enabled: !!token && !!submittalId,
  });
}

export function useCreateSubmittal(
  projectId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SubmittalCreateInput) =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/submittals`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["submittals", portal, projectId] });
    },
  });
}

export function useSubmitSubmittal(
  projectId: string,
  submittalId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/submittals/${submittalId}/submit`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["submittals", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["submittal", "gc", projectId, submittalId] });
    },
  });
}

export function useReviewSubmittal(
  projectId: string,
  submittalId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { decision: string; review_notes?: string }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/submittals/${submittalId}/review`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["submittals", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["submittal", "gc", projectId, submittalId] });
    },
  });
}

export function useReviseSubmittal(
  projectId: string,
  submittalId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { description?: string }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/submittals/${submittalId}/revise`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["submittals", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["submittal", "gc", projectId, submittalId] });
    },
  });
}
