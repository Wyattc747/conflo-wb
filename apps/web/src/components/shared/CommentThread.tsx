"use client";

import { Send } from "lucide-react";
import { useState } from "react";

interface Comment {
  id: string;
  body: string;
  author_name?: string | null;
  author_type: string;
  created_at: string;
  is_official_response?: boolean;
}

interface CommentThreadProps {
  comments: Comment[];
  loading?: boolean;
  onSubmit?: (body: string) => void;
  submitting?: boolean;
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function CommentThread({
  comments,
  loading = false,
  onSubmit,
  submitting = false,
}: CommentThreadProps) {
  const [body, setBody] = useState("");

  const handleSubmit = () => {
    if (!body.trim()) return;
    onSubmit?.(body.trim());
    setBody("");
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900">
          Comments ({comments.length})
        </h3>
      </div>

      {/* Comment list */}
      <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
        {loading ? (
          <div className="px-4 py-8 text-center text-sm text-gray-400">
            Loading comments...
          </div>
        ) : comments.length === 0 ? (
          <div className="px-4 py-8 text-center text-sm text-gray-400">
            No comments yet
          </div>
        ) : (
          comments.map((comment) => (
            <div key={comment.id} className="px-4 py-3">
              <div className="flex items-center gap-2 mb-1">
                <div className="h-6 w-6 rounded-full bg-[#1B2A4A] text-white flex items-center justify-center text-xs font-medium">
                  {(comment.author_name || "?")[0].toUpperCase()}
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {comment.author_name || "Unknown"}
                </span>
                {comment.is_official_response && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-100 text-green-700">
                    Official
                  </span>
                )}
                <span className="text-xs text-gray-400 ml-auto">
                  {formatRelativeTime(comment.created_at)}
                </span>
              </div>
              <p className="text-sm text-gray-700 ml-8">{comment.body}</p>
            </div>
          ))
        )}
      </div>

      {/* Input */}
      {onSubmit && (
        <div className="px-4 py-3 border-t border-gray-200">
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Write a comment..."
              value={body}
              onChange={(e) => setBody(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSubmit()}
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B2A4A]/20 focus:border-[#1B2A4A]"
              disabled={submitting}
            />
            <button
              onClick={handleSubmit}
              disabled={!body.trim() || submitting}
              className="p-2 bg-[#1B2A4A] text-white rounded-lg hover:bg-[#243558] disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
