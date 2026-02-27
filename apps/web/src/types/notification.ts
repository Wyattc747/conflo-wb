export interface Notification {
  id: string;
  type: string;
  title: string;
  body?: string | null;
  source_type?: string | null;
  source_id?: string | null;
  project_id?: string | null;
  metadata?: Record<string, unknown>;
  read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface NotificationPreferences {
  email_enabled: boolean;
  email_categories: {
    assigned_to_me: boolean;
    status_changes: boolean;
    mentions: boolean;
    approaching_deadlines: boolean;
    bid_invitations: boolean;
    pay_app_decisions: boolean;
    meeting_scheduled: boolean;
    meeting_minutes: boolean;
    daily_summary: boolean;
  };
}
