export interface Meeting {
  id: string;
  project_id: string;
  number: number;
  formatted_number: string;
  title: string;
  meeting_type: string;
  status: string;
  scheduled_date?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  location?: string | null;
  virtual_provider?: string | null;
  virtual_link?: string | null;
  attendees: string[];
  agenda?: string | null;
  minutes?: string | null;
  action_items: Record<string, unknown>[];
  recurring: boolean;
  recurrence_rule?: string | null;
  recurrence_end_date?: string | null;
  parent_meeting_id?: string | null;
  minutes_published: boolean;
  minutes_published_at?: string | null;
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MeetingCreateInput {
  title: string;
  meeting_type?: string;
  scheduled_date?: string;
  start_time?: string;
  end_time?: string;
  location?: string;
  virtual_provider?: string;
  virtual_link?: string;
  attendees?: string[];
  agenda?: string;
  recurring?: boolean;
  recurrence_rule?: string;
}

export interface MeetingUpdateInput {
  title?: string;
  meeting_type?: string;
  scheduled_date?: string;
  start_time?: string;
  end_time?: string;
  location?: string;
  attendees?: string[];
  agenda?: string;
  minutes?: string;
  action_items?: Record<string, unknown>[];
}
