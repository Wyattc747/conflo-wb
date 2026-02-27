"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { IntegrationStatus } from "@/types/integration";

export function useIntegrations(token: string | null) {
  return useQuery<{ data: IntegrationStatus[] }>({
    queryKey: ["integrations"],
    queryFn: () => fetchWithAuth("/api/gc/integrations", token!),
    enabled: !!token,
  });
}

export function useConnectIntegration(token: string | null) {
  return useMutation({
    mutationFn: (provider: string) =>
      fetchWithAuth(`/api/gc/integrations/${provider}/connect`, token!, {
        method: "POST",
      }),
  });
}

export function useDisconnectIntegration(token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (provider: string) =>
      fetchWithAuth(`/api/gc/integrations/${provider}/disconnect`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });
}

export function useIntegrationCallback(token: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      provider,
      code,
      state,
      realm_id,
    }: {
      provider: string;
      code: string;
      state?: string;
      realm_id?: string;
    }) =>
      fetchWithAuth(`/api/gc/integrations/${provider}/callback`, token!, {
        method: "POST",
        body: JSON.stringify({ code, state, realm_id }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });
}
