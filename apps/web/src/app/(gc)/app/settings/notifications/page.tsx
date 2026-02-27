"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { Bell, Save } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";
import {
  useNotificationPreferences,
  useUpdateNotificationPreferences,
} from "@/hooks/use-notifications";

const CATEGORY_LABELS: Record<string, { label: string; description: string }> = {
  assigned_to_me: {
    label: "Assigned to me",
    description: "When an item is assigned to you (RFIs, punch list, to-dos)",
  },
  status_changes: {
    label: "Status changes",
    description: "When items you're involved in change status",
  },
  mentions: {
    label: "Mentions",
    description: "When someone mentions you in a comment",
  },
  approaching_deadlines: {
    label: "Approaching deadlines",
    description: "When deadlines are approaching for your items",
  },
  bid_invitations: {
    label: "Bid invitations",
    description: "When bid packages are received or results are in",
  },
  pay_app_decisions: {
    label: "Pay app decisions",
    description: "When pay applications are submitted or decided",
  },
  meeting_scheduled: {
    label: "Meetings scheduled",
    description: "When a new meeting is scheduled",
  },
  meeting_minutes: {
    label: "Meeting minutes",
    description: "When meeting minutes are published",
  },
  daily_summary: {
    label: "Daily summary digest",
    description: "A daily email summarizing all activity",
  },
};

export default function NotificationPreferencesPage() {
  const { getToken } = useAuth();
  const [token, setToken] = useState<string | null>(null);
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [categories, setCategories] = useState<Record<string, boolean>>({});
  const [saved, setSaved] = useState(false);

  if (!token) {
    getToken().then(setToken);
  }

  const { data } = useNotificationPreferences(token);
  const updatePrefs = useUpdateNotificationPreferences(token);

  useEffect(() => {
    if (data?.data) {
      setEmailEnabled(data.data.email_enabled);
      setCategories(data.data.email_categories || {});
    }
  }, [data]);

  const handleSave = () => {
    updatePrefs.mutate(
      { email_enabled: emailEnabled, email_categories: categories },
      {
        onSuccess: () => {
          setSaved(true);
          setTimeout(() => setSaved(false), 2000);
        },
      }
    );
  };

  const toggleCategory = (key: string) => {
    setCategories((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader
        title="Notification Preferences"
        subtitle="Control how and when you receive notifications"
      />

      <Card>
        <div className="p-6 space-y-6">
          {/* Master toggle */}
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-900">Email Notifications</h3>
              <p className="text-xs text-gray-500 mt-0.5">
                Receive email notifications in addition to in-app
              </p>
            </div>
            <button
              onClick={() => setEmailEnabled(!emailEnabled)}
              className={`relative w-11 h-6 rounded-full transition-colors ${
                emailEnabled ? "bg-blue-600" : "bg-gray-300"
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 h-5 w-5 bg-white rounded-full transition-transform ${
                  emailEnabled ? "translate-x-5" : ""
                }`}
              />
            </button>
          </div>

          {emailEnabled && (
            <>
              <hr className="border-gray-100" />
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  Notify me by email when:
                </h3>
                <div className="space-y-3">
                  {Object.entries(CATEGORY_LABELS).map(([key, { label, description }]) => (
                    <label
                      key={key}
                      className="flex items-start gap-3 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={categories[key] ?? true}
                        onChange={() => toggleCategory(key)}
                        className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{label}</p>
                        <p className="text-xs text-gray-500">{description}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </>
          )}

          <hr className="border-gray-100" />

          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-500">
              In-app notifications are always enabled for all categories.
            </p>
            <button
              onClick={handleSave}
              disabled={updatePrefs.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <Save className="h-4 w-4" />
              {saved ? "Saved!" : "Save Preferences"}
            </button>
          </div>
        </div>
      </Card>
    </div>
  );
}
