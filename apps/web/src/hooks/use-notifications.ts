"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { Notification, NotificationPreferences } from "@/types/notification";
import type { ListResponse } from "@/types/common";

export function useNotifications(
  token: string | null,
  portalPrefix: string = "/api/gc",
  params?: {
    page?: number;
    per_page?: number;
    unread_only?: boolean;
  }
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.unread_only) queryParams.set("unread_only", "true");

  return useQuery<ListResponse<Notification>>({
    queryKey: ["notifications", portalPrefix, params],
    queryFn: () =>
      fetchWithAuth(
        `${portalPrefix}/notifications?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useUnreadCount(
  token: string | null,
  portalPrefix: string = "/api/gc"
) {
  return useQuery<{ data: { count: number } }>({
    queryKey: ["notifications-unread", portalPrefix],
    queryFn: () =>
      fetchWithAuth(`${portalPrefix}/notifications/unread-count`, token!),
    enabled: !!token,
    refetchInterval: 30000, // Poll every 30 seconds
  });
}

export function useMarkRead(
  token: string | null,
  portalPrefix: string = "/api/gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) =>
      fetchWithAuth(
        `${portalPrefix}/notifications/${notificationId}/read`,
        token!,
        { method: "POST" }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread"] });
    },
  });
}

export function useMarkAllRead(
  token: string | null,
  portalPrefix: string = "/api/gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`${portalPrefix}/notifications/read-all`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread"] });
    },
  });
}

export function useDismissNotification(
  token: string | null,
  portalPrefix: string = "/api/gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) =>
      fetchWithAuth(
        `${portalPrefix}/notifications/${notificationId}`,
        token!,
        { method: "DELETE" }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread"] });
    },
  });
}

export function useNotificationPreferences(
  token: string | null,
  portalPrefix: string = "/api/gc"
) {
  return useQuery<{ data: NotificationPreferences }>({
    queryKey: ["notification-preferences", portalPrefix],
    queryFn: () =>
      fetchWithAuth(`${portalPrefix}/notifications/preferences`, token!),
    enabled: !!token,
  });
}

export function useUpdateNotificationPreferences(
  token: string | null,
  portalPrefix: string = "/api/gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<NotificationPreferences>) =>
      fetchWithAuth(`${portalPrefix}/notifications/preferences`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
    },
  });
}
