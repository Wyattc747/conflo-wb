"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { Meeting, MeetingCreateInput, MeetingUpdateInput } from "@/types/meeting";
import type { ListResponse } from "@/types/common";

export function useMeetings(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    status?: string;
    meeting_type?: string;
    search?: string;
    sort?: string;
    order?: string;
  }
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.status) queryParams.set("status", params.status);
  if (params?.meeting_type) queryParams.set("meeting_type", params.meeting_type);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<Meeting>>({
    queryKey: ["meetings", projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/gc/projects/${projectId}/meetings?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useMeeting(
  projectId: string,
  meetingId: string,
  token: string | null
) {
  return useQuery<{ data: Meeting }>({
    queryKey: ["meeting", projectId, meetingId],
    queryFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/meetings/${meetingId}`, token!),
    enabled: !!token && !!meetingId,
  });
}

export function useCreateMeeting(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MeetingCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/meetings`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings", projectId] });
    },
  });
}

export function useUpdateMeeting(
  projectId: string,
  meetingId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MeetingUpdateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/meetings/${meetingId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings", projectId] });
      queryClient.invalidateQueries({ queryKey: ["meeting", projectId, meetingId] });
    },
  });
}

export function useDeleteMeeting(
  projectId: string,
  meetingId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/meetings/${meetingId}`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings", projectId] });
    },
  });
}

export function useStartMeeting(
  projectId: string,
  meetingId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/meetings/${meetingId}/start`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings", projectId] });
      queryClient.invalidateQueries({ queryKey: ["meeting", projectId, meetingId] });
    },
  });
}

export function useCompleteMeeting(
  projectId: string,
  meetingId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/meetings/${meetingId}/complete`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings", projectId] });
      queryClient.invalidateQueries({ queryKey: ["meeting", projectId, meetingId] });
    },
  });
}

export function useCancelMeeting(
  projectId: string,
  meetingId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/meetings/${meetingId}/cancel`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings", projectId] });
      queryClient.invalidateQueries({ queryKey: ["meeting", projectId, meetingId] });
    },
  });
}

export function usePublishMinutes(
  projectId: string,
  meetingId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { minutes: string; action_items?: Record<string, unknown>[] }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/meetings/${meetingId}/publish-minutes`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings", projectId] });
      queryClient.invalidateQueries({ queryKey: ["meeting", projectId, meetingId] });
    },
  });
}

export function useGenerateRecurring(
  projectId: string,
  meetingId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (count?: number) =>
      fetchWithAuth(
        `/api/gc/projects/${projectId}/meetings/${meetingId}/generate-recurring${count ? `?count=${count}` : ""}`,
        token!,
        { method: "POST" }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings", projectId] });
    },
  });
}
