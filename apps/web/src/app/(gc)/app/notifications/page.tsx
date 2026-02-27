"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { Bell, CheckCheck, ChevronRight } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";
import { useNotifications, useMarkRead, useMarkAllRead, useDismissNotification } from "@/hooks/use-notifications";
import type { Notification } from "@/types/notification";

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString();
}

function getEntityRoute(n: Notification): string | null {
  if (!n.source_type || !n.project_id) return null;
  const routes: Record<string, string> = {
    rfi: `/app/projects/${n.project_id}/rfis/${n.source_id}`,
    submittal: `/app/projects/${n.project_id}/submittals/${n.source_id}`,
    change_order: `/app/projects/${n.project_id}/change-orders/${n.source_id}`,
    pay_app: `/app/projects/${n.project_id}/pay-apps/${n.source_id}`,
    punch_list_item: `/app/projects/${n.project_id}/punch-list/${n.source_id}`,
    meeting: `/app/projects/${n.project_id}/meetings/${n.source_id}`,
    todo: `/app/projects/${n.project_id}/todos/${n.source_id}`,
    bid_package: `/app/projects/${n.project_id}/bid-packages/${n.source_id}`,
  };
  return routes[n.source_type] || null;
}

export default function NotificationsPage() {
  const { getToken } = useAuth();
  const [token, setToken] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "unread">("all");
  const [page, setPage] = useState(1);
  const router = useRouter();

  if (!token) {
    getToken().then(setToken);
  }

  const { data, isLoading } = useNotifications(token, "/api/gc", {
    page,
    per_page: 25,
    unread_only: filter === "unread",
  });
  const markRead = useMarkRead(token);
  const markAllRead = useMarkAllRead(token);
  const dismiss = useDismissNotification(token);

  const notifications = data?.data || [];
  const meta = data?.meta;

  const handleClick = (n: Notification) => {
    if (!n.read) markRead.mutate(n.id);
    const route = getEntityRoute(n);
    if (route) router.push(route);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader title="Notifications" subtitle="Stay updated on project activity" />

      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          <button
            onClick={() => { setFilter("all"); setPage(1); }}
            className={`px-3 py-1.5 text-sm rounded-full font-medium transition-colors ${
              filter === "all" ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            All
          </button>
          <button
            onClick={() => { setFilter("unread"); setPage(1); }}
            className={`px-3 py-1.5 text-sm rounded-full font-medium transition-colors ${
              filter === "unread" ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            Unread
          </button>
        </div>
        <button
          onClick={() => markAllRead.mutate()}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
        >
          <CheckCheck className="h-4 w-4" />
          Mark all read
        </button>
      </div>

      <Card>
        {isLoading ? (
          <div className="py-8 text-center text-sm text-gray-500">Loading...</div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center py-8 text-center">
            <Bell className="h-10 w-10 text-gray-300 mb-3" />
            <h3 className="text-base font-semibold text-gray-900 mb-1">
              {filter === "unread" ? "No unread notifications" : "No notifications"}
            </h3>
            <p className="text-sm text-gray-500">
              {filter === "unread" ? "You're all caught up!" : "New notifications will appear here."}
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {notifications.map((n) => (
              <li
                key={n.id}
                onClick={() => handleClick(n)}
                className={`px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors flex items-center gap-3 ${
                  !n.read ? "bg-blue-50/50" : ""
                }`}
              >
                {!n.read && (
                  <span className="h-2 w-2 bg-blue-500 rounded-full flex-shrink-0" />
                )}
                <div className={`flex-1 min-w-0 ${n.read ? "ml-5" : ""}`}>
                  <p className="text-sm font-medium text-gray-900">{n.title}</p>
                  {n.body && (
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.body}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">{timeAgo(n.created_at)}</p>
                </div>
                <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0" />
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* Pagination */}
      {meta && meta.total_pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-gray-500">
            Page {meta.page} of {meta.total_pages} ({meta.total} total)
          </p>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1.5 text-sm rounded border border-gray-300 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              disabled={page >= meta.total_pages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 text-sm rounded border border-gray-300 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
