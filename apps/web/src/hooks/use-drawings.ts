"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type {
  DrawingSet,
  DrawingSetCreateInput,
  DrawingSetUpdateInput,
} from "@/types/drawing";
import type { ListResponse } from "@/types/common";

export function useDrawingSets(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    discipline?: string;
    is_current_set?: boolean;
    search?: string;
    sort?: string;
    order?: string;
  },
  portal: "gc" | "sub" | "owner" = "gc"
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.discipline) queryParams.set("discipline", params.discipline);
  if (params?.is_current_set !== undefined)
    queryParams.set("is_current_set", String(params.is_current_set));
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<DrawingSet>>({
    queryKey: ["drawing-sets", portal, projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/${portal}/projects/${projectId}/drawings?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useDrawingSet(
  projectId: string,
  drawingId: string,
  token: string | null,
  portal: "gc" | "sub" | "owner" = "gc"
) {
  return useQuery<{ data: DrawingSet }>({
    queryKey: ["drawing-set", portal, projectId, drawingId],
    queryFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/drawings/${drawingId}`, token!),
    enabled: !!token && !!drawingId,
  });
}

export function useCreateDrawingSet(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DrawingSetCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/drawings`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drawing-sets", "gc", projectId] });
    },
  });
}

export function useUpdateDrawingSet(
  projectId: string,
  drawingId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DrawingSetUpdateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/drawings/${drawingId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drawing-sets", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["drawing-set", "gc", projectId, drawingId] });
    },
  });
}

export function useDeleteDrawingSet(
  projectId: string,
  drawingId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/drawings/${drawingId}`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drawing-sets", "gc", projectId] });
    },
  });
}

export function useMarkCurrentSet(
  projectId: string,
  drawingId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/drawings/${drawingId}/mark-current`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drawing-sets", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["drawing-set", "gc", projectId, drawingId] });
    },
  });
}

export function useAddSheet(
  projectId: string,
  drawingId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { sheet_number: string; title?: string; description?: string; revision?: string; file_id?: string }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/drawings/${drawingId}/sheets`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drawing-set", "gc", projectId, drawingId] });
    },
  });
}

export function useReviseSheet(
  projectId: string,
  drawingId: string,
  sheetId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { revision: string; file_id?: string }) =>
      fetchWithAuth(
        `/api/gc/projects/${projectId}/drawings/${drawingId}/sheets/${sheetId}/revise?revision=${data.revision}${data.file_id ? `&file_id=${data.file_id}` : ""}`,
        token!,
        { method: "POST" }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drawing-set", "gc", projectId, drawingId] });
    },
  });
}
