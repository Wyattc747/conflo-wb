"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type {
  BidPackage,
  BidPackageCreateInput,
  BidPackageUpdateInput,
  BidSubmissionCreateInput,
  BidComparisonResponse,
  BidSubmission,
} from "@/types/bid-package";
import type { ListResponse } from "@/types/common";

export function useBidPackages(
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

  return useQuery<ListResponse<BidPackage>>({
    queryKey: ["bid-packages", projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/gc/projects/${projectId}/bid-packages?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useBidPackage(
  projectId: string,
  packageId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const path =
    portal === "sub"
      ? `/api/sub/bid-packages/${packageId}`
      : `/api/gc/projects/${projectId}/bid-packages/${packageId}`;

  return useQuery<{ data: BidPackage }>({
    queryKey: ["bid-package", portal, projectId, packageId],
    queryFn: () => fetchWithAuth(path, token!),
    enabled: !!token && !!packageId,
  });
}

export function useCreateBidPackage(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BidPackageCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/bid-packages`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-packages", projectId] });
    },
  });
}

export function useUpdateBidPackage(
  projectId: string,
  packageId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BidPackageUpdateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/bid-packages/${packageId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-packages", projectId] });
      queryClient.invalidateQueries({ queryKey: ["bid-package", "gc", projectId, packageId] });
    },
  });
}

export function useDeleteBidPackage(
  projectId: string,
  packageId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/bid-packages/${packageId}`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-packages", projectId] });
    },
  });
}

export function useDistributeBidPackage(
  projectId: string,
  packageId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { sub_company_ids: string[] }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/bid-packages/${packageId}/distribute`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-packages", projectId] });
      queryClient.invalidateQueries({ queryKey: ["bid-package", "gc", projectId, packageId] });
    },
  });
}

export function useCloseBidding(
  projectId: string,
  packageId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/bid-packages/${packageId}/close`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-packages", projectId] });
      queryClient.invalidateQueries({ queryKey: ["bid-package", "gc", projectId, packageId] });
    },
  });
}

export function useCompareBids(
  projectId: string,
  packageId: string,
  token: string | null
) {
  return useQuery<{ data: BidComparisonResponse }>({
    queryKey: ["bid-comparison", projectId, packageId],
    queryFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/bid-packages/${packageId}/compare`, token!),
    enabled: !!token && !!packageId,
  });
}

export function useAwardBid(
  projectId: string,
  packageId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { sub_company_id: string }) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/bid-packages/${packageId}/award`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-packages", projectId] });
      queryClient.invalidateQueries({ queryKey: ["bid-package", "gc", projectId, packageId] });
    },
  });
}

export function useBidSubmissions(
  projectId: string,
  packageId: string,
  token: string | null
) {
  return useQuery<ListResponse<BidSubmission>>({
    queryKey: ["bid-submissions", projectId, packageId],
    queryFn: () =>
      fetchWithAuth(`/api/gc/projects/${projectId}/bid-packages/${packageId}/submissions`, token!),
    enabled: !!token && !!packageId,
  });
}

// Sub portal hooks

export function useSubCreateSubmission(
  packageId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BidSubmissionCreateInput) =>
      fetchWithAuth(`/api/sub/bid-packages/${packageId}/submissions`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-package", "sub"] });
    },
  });
}

export function useSubSubmitBid(
  packageId: string,
  submissionId: string,
  token: string | null
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/sub/bid-packages/${packageId}/submissions/${submissionId}/submit`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bid-package", "sub"] });
    },
  });
}

export function useSubMySubmission(
  packageId: string,
  token: string | null
) {
  return useQuery<{ data: BidSubmission }>({
    queryKey: ["bid-my-submission", packageId],
    queryFn: () =>
      fetchWithAuth(`/api/sub/bid-packages/${packageId}/my-submission`, token!),
    enabled: !!token && !!packageId,
  });
}
