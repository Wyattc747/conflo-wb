"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { DailyLog, DailyLogCreateInput, DailyLogUpdateInput } from "@/types/daily-log";
import type { ListResponse } from "@/types/common";

export function useDailyLogs(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    status?: string;
    search?: string;
    sort?: string;
    order?: string;
  }
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.status) queryParams.set("status", params.status);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<DailyLog>>({
    queryKey: ["daily-logs", projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/gc/projects/${projectId}/daily-logs?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useDailyLog(projectId: string, logId: string, token: string | null) {
  return useQuery<{ data: DailyLog }>({
    queryKey: ["daily-log", projectId, logId],
    queryFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/daily-logs/${logId}`, token!),
    enabled: !!token && !!logId,
  });
}

export function useCreateDailyLog(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DailyLogCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/daily-logs`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["daily-logs", projectId] });
    },
  });
}

export function useUpdateDailyLog(projectId: string, logId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DailyLogUpdateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/daily-logs/${logId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["daily-logs", projectId] });
      queryClient.invalidateQueries({ queryKey: ["daily-log", projectId, logId] });
    },
  });
}

export function useSubmitDailyLog(projectId: string, logId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/daily-logs/${logId}/submit`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["daily-logs", projectId] });
      queryClient.invalidateQueries({ queryKey: ["daily-log", projectId, logId] });
    },
  });
}

export function useApproveDailyLog(projectId: string, logId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/daily-logs/${logId}/approve`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["daily-logs", projectId] });
      queryClient.invalidateQueries({ queryKey: ["daily-log", projectId, logId] });
    },
  });
}

export function useDeleteDailyLog(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (logId: string) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/daily-logs/${logId}`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["daily-logs", projectId] });
    },
  });
}
