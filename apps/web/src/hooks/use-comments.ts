"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import type { Comment } from "@/types/comment";
import type { ListResponse } from "@/types/common";

export function useComments(
  projectId: string,
  commentableType: string,
  commentableId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const queryParams = new URLSearchParams({
    commentable_type: commentableType,
    commentable_id: commentableId,
    per_page: "100",
  });

  return useQuery<ListResponse<Comment>>({
    queryKey: ["comments", portal, projectId, commentableType, commentableId],
    queryFn: () =>
      fetchWithAuth(
        `/api/${portal}/projects/${projectId}/comments?${queryParams}`,
        token!
      ),
    enabled: !!token && !!commentableId,
  });
}

export function useCreateComment(
  projectId: string,
  commentableType: string,
  commentableId: string,
  token: string | null,
  portal: "gc" | "sub" = "gc"
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      fetchWithAuth(`/api/${portal}/projects/${projectId}/comments`, token!, {
        method: "POST",
        body: JSON.stringify({
          commentable_type: commentableType,
          commentable_id: commentableId,
          body,
          mentions: [],
          attachments: [],
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["comments", portal, projectId, commentableType, commentableId],
      });
    },
  });
}
