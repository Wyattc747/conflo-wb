"use client";

import { Bell } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function NotificationsPage() {
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader title="Notifications" subtitle="Stay updated on project activity" />
      <Card>
        <div className="flex flex-col items-center py-8 text-center">
          <Bell className="h-10 w-10 text-gray-300 mb-3" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">No notifications</h3>
          <p className="text-sm text-gray-500">You&apos;re all caught up! New notifications will appear here.</p>
        </div>
      </Card>
    </div>
  );
}
