export interface RFI {
  id: string;
  project_id: string;
  number: number;
  formatted_number: string;
  subject: string;
  question: string;
  official_response?: string | null;
  status: string;
  priority: string;
  assigned_to?: string | null;
  assigned_to_name?: string | null;
  due_date?: string | null;
  days_open?: number | null;
  cost_impact: boolean;
  schedule_impact: boolean;
  drawing_reference?: string | null;
  spec_section?: string | null;
  location?: string | null;
  created_by?: string | null;
  created_by_name?: string | null;
  responded_by?: string | null;
  responded_by_name?: string | null;
  responded_at?: string | null;
  created_at: string;
  updated_at: string;
  comments_count: number;
}

export interface RFICreateInput {
  subject: string;
  question: string;
  assigned_to?: string;
  due_date?: string;
  priority?: string;
  cost_impact?: boolean;
  schedule_impact?: boolean;
}

export interface RFIUpdateInput {
  subject?: string;
  question?: string;
  assigned_to?: string;
  due_date?: string;
  priority?: string;
  cost_impact?: boolean;
  schedule_impact?: boolean;
}
