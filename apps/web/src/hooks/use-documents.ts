"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type {
  Document,
  DocumentCreateInput,
  DocumentUpdateInput,
  DocumentFolder,
} from "@/types/document";
import type { ListResponse } from "@/types/common";

export function useDocuments(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    folder_id?: string;
    category?: string;
    search?: string;
    sort?: string;
    order?: string;
  },
  portal: "gc" | "sub" = "gc"
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.folder_id) queryParams.set("folder_id", params.folder_id);
  if (params?.category) queryParams.set("category", params.category);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  const prefix = portal === "sub" ? "sub" : "gc";

  return useQuery<ListResponse<Document>>({
    queryKey: ["documents", portal, projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/${prefix}/projects/${projectId}/documents?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useDocument(
  projectId: string,
  documentId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const prefix = portal === "sub" ? "sub" : "gc";
  return useQuery<{ data: Document }>({
    queryKey: ["document", portal, projectId, documentId],
    queryFn: () =>
      fetchWithAuth(`/api/${prefix}/projects/${projectId}/documents/${documentId}`, token!),
    enabled: !!token && !!documentId,
  });
}

export function useCreateDocument(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DocumentCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/documents`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", "gc", projectId] });
    },
  });
}

export function useUpdateDocument(
  projectId: string,
  documentId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DocumentUpdateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/documents/${documentId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["document", "gc", projectId, documentId] });
    },
  });
}

export function useDeleteDocument(
  projectId: string,
  documentId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/documents/${documentId}`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", "gc", projectId] });
    },
  });
}

export function useUploadNewVersion(
  projectId: string,
  documentId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { file_id: string }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/documents/${documentId}/new-version`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", "gc", projectId] });
      queryClient.invalidateQueries({ queryKey: ["document", "gc", projectId, documentId] });
    },
  });
}

// Folder hooks

export function useDocumentFolders(
  projectId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const prefix = portal === "sub" ? "sub" : "gc";
  return useQuery<{ data: DocumentFolder[] }>({
    queryKey: ["document-folders", portal, projectId],
    queryFn: () =>
      fetchWithAuth(`/api/${prefix}/projects/${projectId}/documents/folders`, token!),
    enabled: !!token,
  });
}

export function useCreateFolder(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; parent_folder_id?: string }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/documents/folders`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document-folders", "gc", projectId] });
    },
  });
}

export function useDeleteFolder(
  projectId: string,
  folderId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/documents/folders/${folderId}`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document-folders", "gc", projectId] });
    },
  });
}
