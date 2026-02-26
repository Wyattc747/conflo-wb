"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type {
  ScheduleTask,
  ScheduleTaskCreateInput,
  ScheduleDelay,
  ScheduleVersion,
  ScheduleConfig,
  ScheduleHealth,
} from "@/types/schedule";
import type { ListResponse } from "@/types/common";

// --- Tasks ---

export function useScheduleTasks(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    search?: string;
    sort?: string;
    order?: string;
  },
  portal: "gc" | "sub" | "owner" = "gc"
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<ScheduleTask>>({
    queryKey: ["schedule-tasks", portal, projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/${portal}/projects/${projectId}/schedule/tasks?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useCreateTask(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ScheduleTaskCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/schedule/tasks`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-tasks", "gc", projectId] });
    },
  });
}

export function useUpdateTask(
  projectId: string,
  taskId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ScheduleTaskCreateInput> & { percent_complete?: number }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/schedule/tasks/${taskId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-tasks", "gc", projectId] });
    },
  });
}

// --- Baseline & Publish ---

export function useLockBaseline(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/schedule/lock-baseline`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-tasks", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["schedule-health", projectId] });
    },
  });
}

export function usePublishSchedule(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { version_type: string; title: string; notes?: string }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/schedule/publish`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-versions", projectId] });
    },
  });
}

// --- Health ---

export function useScheduleHealth(projectId: string, token: string | null) {
  return useQuery<{ data: ScheduleHealth }>({
    queryKey: ["schedule-health", projectId],
    queryFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/schedule/health`, token!),
    enabled: !!token,
  });
}

// --- Config ---

export function useScheduleConfig(projectId: string, token: string | null) {
  return useQuery<{ data: ScheduleConfig }>({
    queryKey: ["schedule-config", projectId],
    queryFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/schedule/config`, token!),
    enabled: !!token,
  });
}

export function useUpdateConfig(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ScheduleConfig>) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/schedule/config`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-config", projectId] });
    },
  });
}

// --- Delays ---

export function useScheduleDelays(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    status?: string;
    sort?: string;
    order?: string;
  }
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.status) queryParams.set("status", params.status);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<ScheduleDelay>>({
    queryKey: ["schedule-delays", projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/gc/projects/${projectId}/schedule/delays?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useCreateDelay(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      task_ids: string[];
      delay_days: number;
      reason_category: string;
      responsible_party: string;
      description: string;
    }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/schedule/delays`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-delays", projectId] });
    },
  });
}

export function useApproveDelay(
  projectId: string,
  delayId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/schedule/delays/${delayId}/approve`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-delays", projectId] });
    },
  });
}

export function useApplyDelay(
  projectId: string,
  delayId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/schedule/delays/${delayId}/apply`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-delays", projectId] });
      queryClient.invalidateQueries({ queryKey: ["schedule-tasks", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["schedule-health", projectId] });
    },
  });
}

// --- Versions ---

export function useScheduleVersions(projectId: string, token: string | null) {
  return useQuery<ListResponse<ScheduleVersion>>({
    queryKey: ["schedule-versions", projectId],
    queryFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/schedule/versions`, token!),
    enabled: !!token,
  });
}

// --- Look Ahead ---

export function useLookAheadTasks(
  projectId: string,
  token: string | null,
  params?: { weeks?: number }
) {
  const queryParams = new URLSearchParams();
  if (params?.weeks) queryParams.set("weeks", String(params.weeks));

  return useQuery<ListResponse<ScheduleTask>>({
    queryKey: ["look-ahead", projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/gc/projects/${projectId}/schedule/look-ahead?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}
