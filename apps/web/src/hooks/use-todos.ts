"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { Todo, TodoCreateInput, TodoUpdateInput } from "@/types/todo";
import type { ListResponse } from "@/types/common";

export function useTodos(
  projectId: string,
  token: string | null,
  params?: {
    page?: number;
    per_page?: number;
    status?: string;
    priority?: string;
    assigned_to?: string;
    category?: string;
    source_type?: string;
    search?: string;
    sort?: string;
    order?: string;
  },
  portal: "gc" | "sub" = "gc"
) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", String(params.page));
  if (params?.per_page) queryParams.set("per_page", String(params.per_page));
  if (params?.status) queryParams.set("status", params.status);
  if (params?.priority) queryParams.set("priority", params.priority);
  if (params?.assigned_to) queryParams.set("assigned_to", params.assigned_to);
  if (params?.category) queryParams.set("category", params.category);
  if (params?.source_type) queryParams.set("source_type", params.source_type);
  if (params?.search) queryParams.set("search", params.search);
  if (params?.sort) queryParams.set("sort", params.sort);
  if (params?.order) queryParams.set("order", params.order);

  return useQuery<ListResponse<Todo>>({
    queryKey: ["todos", portal, projectId, params],
    queryFn: () =>
      fetchWithAuth(
        `/api/${portal}/projects/${projectId}/todos?${queryParams}`,
        token!
      ),
    enabled: !!token,
  });
}

export function useTodo(
  projectId: string,
  todoId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  return useQuery<{ data: Todo }>({
    queryKey: ["todo", portal, projectId, todoId],
    queryFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/todos/${todoId}`, token!),
    enabled: !!token && !!todoId,
  });
}

export function useCreateTodo(
  projectId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TodoCreateInput) =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/todos`, token!, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos", portal, projectId] });
    },
  });
}

export function useUpdateTodo(
  projectId: string,
  todoId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TodoUpdateInput) =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/todos/${todoId}`, token!, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos", portal, projectId] });
      queryClient.invalidateQueries({ queryKey: ["todo", portal, projectId, todoId] });
    },
  });
}

export function useDeleteTodo(
  projectId: string,
  todoId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/todos/${todoId}`, token!, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos", portal, projectId] });
    },
  });
}

export function useStartTodo(
  projectId: string,
  todoId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/todos/${todoId}/start`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos", portal, projectId] });
      queryClient.invalidateQueries({ queryKey: ["todo", portal, projectId, todoId] });
    },
  });
}

export function useCompleteTodo(
  projectId: string,
  todoId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/todos/${todoId}/complete`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos", portal, projectId] });
      queryClient.invalidateQueries({ queryKey: ["todo", portal, projectId, todoId] });
    },
  });
}

export function useReopenTodo(
  projectId: string,
  todoId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/todos/${todoId}/reopen`, token!, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos", portal, projectId] });
      queryClient.invalidateQueries({ queryKey: ["todo", portal, projectId, todoId] });
    },
  });
}
