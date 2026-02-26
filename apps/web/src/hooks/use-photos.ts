"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { Photo, PhotoCreateInput, PhotoUpdateInput } from "@/types/photo";
import type { ListResponse } from "@/types/common";

export function usePhotos(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    linked_type?: string;
    linked_id?: string;
    date_from?: string;
    date_to?: string;
    search?: string;
    sort?: string;
    order?: string;
  },
  portal: "gc" | "sub" = "gc"
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.linked_type) queryParams.set("linked_type", params.linked_type);
  if (params?.linked_id) queryParams.set("linked_id", params.linked_id);
  if (params?.date_from) queryParams.set("date_from", params.date_from);
  if (params?.date_to) queryParams.set("date_to", params.date_to);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<Photo>>({
    queryKey: ["photos", portal, projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/${portal}/projects/${projectId}/photos?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function usePhoto(
  projectId: string,
  photoId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  return useQuery<{ data: Photo }>({
    queryKey: ["photo", portal, projectId, photoId],
    queryFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/photos/${photoId}`, token!),
    enabled: !!token && !!photoId,
  });
}

export function useCreatePhoto(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PhotoCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/photos`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["photos", "gc", projectId] });
    },
  });
}

export function useUpdatePhoto(
  projectId: string,
  photoId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PhotoUpdateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/photos/${photoId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["photos", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["photo", "gc", projectId, photoId] });
    },
  });
}

export function useDeletePhoto(
  projectId: string,
  photoId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/photos/${photoId}`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["photos", "gc", projectId] });
    },
  });
}
