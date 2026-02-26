"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type {
  InspectionTemplate,
  Inspection,
  InspectionCreateInput,
} from "@/types/inspection";
import type { ListResponse } from "@/types/common";

export function useInspectionTemplates(token: string | null) {
  return useQuery<ListResponse<InspectionTemplate>>({
    queryKey: ["inspection-templates"],
    queryFn: () =>
      fetchWithAuth("/api/gc/inspection-templates", token!),
    enabled: !!token,
  });
}

export function useCreateTemplate(token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string; category: string; checklist_items: { label: string; required: boolean; order: number }[] }) =>
      fetchWithAuth("/api/gc/inspection-templates", token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspection-templates"] });
    },
  });
}

export function useInspections(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    status?: string;
    category?: string;
    search?: string;
    sort?: string;
    order?: string;
  }
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.status) queryParams.set("status", params.status);
  if (params?.category) queryParams.set("category", params.category);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<Inspection>>({
    queryKey: ["inspections", projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/gc/projects/${projectId}/inspections?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useInspection(
  projectId: string,
  inspectionId: string,
  token: string | null
) {
  return useQuery<{ data: Inspection }>({
    queryKey: ["inspection", projectId, inspectionId],
    queryFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/inspections/${inspectionId}`, token!),
    enabled: !!token && !!inspectionId,
  });
}

export function useCreateInspection(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InspectionCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/inspections`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspections", projectId] });
    },
  });
}

export function useStartInspection(
  projectId: string,
  inspectionId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/inspections/${inspectionId}/start`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspections", projectId] });
      queryClient.invalidateQueries({ queryKey: ["inspection", projectId, inspectionId] });
    },
  });
}

export function useCompleteInspection(
  projectId: string,
  inspectionId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { overall_result: string; checklist_results?: { item_label: string; result: string; notes?: string }[]; notes?: string }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/inspections/${inspectionId}/complete`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspections", projectId] });
      queryClient.invalidateQueries({ queryKey: ["inspection", projectId, inspectionId] });
    },
  });
}
