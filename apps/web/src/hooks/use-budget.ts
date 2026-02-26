"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { BudgetSummary, BudgetLineItemCreateInput, BudgetLineItemUpdateInput } from "@/types/budget";

export function useBudget(projectId: string, token: string | null) {
  return useQuery<{ data: BudgetSummary }>({
    queryKey: ["budget", projectId],
    queryFn: () => fetchWithAuth(`/api/gc/projects/${projectId}/budget`, token!),
    enabled: !!token,
  });
}

export function useCreateBudgetLineItem(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BudgetLineItemCreateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/budget/line-items`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget", projectId] });
    },
  });
}

export function useUpdateBudgetLineItem(projectId: string, itemId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BudgetLineItemUpdateInput) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/budget/line-items/${itemId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget", projectId] });
    },
  });
}

export function useDeleteBudgetLineItem(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/budget/line-items/${itemId}`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget", projectId] });
    },
  });
}

export function useImportBudget(projectId: string, token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (items: BudgetLineItemCreateInput[]) =>
      fetchWithAuth(`/api/gc/projects/${projectId}/budget/import`, token!, {
        method: "POST",
        body: JSON.stringify(items),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget", projectId] });
    },
  });
}
