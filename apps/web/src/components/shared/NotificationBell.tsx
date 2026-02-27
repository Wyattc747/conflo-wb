"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Bell, Check, CheckCheck } from "lucide-react";
import { useUnreadCount, useNotifications, useMarkRead, useMarkAllRead } from "@/hooks/use-notifications";
import type { Notification } from "@/types/notification";

const TYPE_LABELS: Record<string, string> = {
  rfi_assigned: "RFI Assigned",
  punch_assigned: "Punch List Assigned",
  todo_assigned: "To-Do Assigned",
  project_assigned: "Project Assigned",
  rfi_response: "RFI Response",
  submittal_decision: "Submittal Decision",
  co_approved: "Change Order Approved",
  co_rejected: "Change Order Rejected",
  pay_app_approved: "Pay App Approved",
  pay_app_rejected: "Pay App Rejected",
  comment_mention: "Mentioned in Comment",
  rfi_due_approaching: "RFI Due Soon",
  bid_deadline_approaching: "Bid Deadline",
  invited_to_bid: "Bid Invitation",
  meeting_scheduled: "Meeting Scheduled",
  meeting_minutes: "Minutes Published",
};

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

function getEntityRoute(n: Notification, prefix: string): string | null {
  if (!n.source_type || !n.project_id) return null;
  const routes: Record<string, string> = {
    rfi: `${prefix}/projects/${n.project_id}/rfis/${n.source_id}`,
    submittal: `${prefix}/projects/${n.project_id}/submittals/${n.source_id}`,
    change_order: `${prefix}/projects/${n.project_id}/change-orders/${n.source_id}`,
    pay_app: `${prefix}/projects/${n.project_id}/pay-apps/${n.source_id}`,
    punch_list_item: `${prefix}/projects/${n.project_id}/punch-list/${n.source_id}`,
    meeting: `${prefix}/projects/${n.project_id}/meetings/${n.source_id}`,
    todo: `${prefix}/projects/${n.project_id}/todos/${n.source_id}`,
    bid_package: `${prefix}/projects/${n.project_id}/bid-packages/${n.source_id}`,
  };
  return routes[n.source_type] || null;
}

interface NotificationBellProps {
  token: string | null;
  portalPrefix?: string;
  routePrefix?: string;
}

export function NotificationBell({
  token,
  portalPrefix = "/api/gc",
  routePrefix = "/app",
}: NotificationBellProps) {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const { data: countData } = useUnreadCount(token, portalPrefix);
  const { data: notifData } = useNotifications(token, portalPrefix, {
    page: 1,
    per_page: 10,
  });
  const markRead = useMarkRead(token, portalPrefix);
  const markAllRead = useMarkAllRead(token, portalPrefix);

  const unreadCount = countData?.data?.count || 0;
  const notifications = notifData?.data || [];

  const handleClick = (n: Notification) => {
    if (!n.read) {
      markRead.mutate(n.id);
    }
    const route = getEntityRoute(n, routePrefix);
    if (route) {
      router.push(route);
    }
    setOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="text-white hover:text-yellow-300 relative"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full text-[10px] text-white flex items-center justify-center font-medium">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />

          {/* Dropdown */}
          <div className="absolute right-0 top-full mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-[480px] overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
              <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllRead.mutate()}
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                >
                  <CheckCheck className="h-3 w-3" />
                  Mark all read
                </button>
              )}
            </div>

            <div className="overflow-y-auto max-h-[380px]">
              {notifications.length === 0 ? (
                <div className="py-8 text-center">
                  <Bell className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">No notifications yet</p>
                </div>
              ) : (
                <ul className="divide-y divide-gray-50">
                  {notifications.map((n) => (
                    <li
                      key={n.id}
                      onClick={() => handleClick(n)}
                      className={`px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                        !n.read ? "bg-blue-50/50" : ""
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {!n.read && (
                          <span className="mt-1.5 h-2 w-2 bg-blue-500 rounded-full flex-shrink-0" />
                        )}
                        <div className={`flex-1 min-w-0 ${n.read ? "ml-5" : ""}`}>
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {n.title}
                          </p>
                          {n.body && (
                            <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                              {n.body}
                            </p>
                          )}
                          <p className="text-xs text-gray-400 mt-1">
                            {timeAgo(n.created_at)}
                          </p>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="border-t border-gray-100 px-4 py-2">
              <button
                onClick={() => {
                  router.push(`${routePrefix}/notifications`);
                  setOpen(false);
                }}
                className="text-xs text-blue-600 hover:text-blue-700 font-medium w-full text-center"
              >
                View all notifications
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
