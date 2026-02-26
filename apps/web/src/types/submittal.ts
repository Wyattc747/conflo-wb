export interface Submittal {
  id: string;
  project_id: string;
  number: number;
  revision: number;
  formatted_number: string;
  title: string;
  spec_section?: string | null;
  description?: string | null;
  submittal_type?: string | null;
  status: string;
  sub_company_id?: string | null;
  sub_company_name?: string | null;
  assigned_to?: string | null;
  assigned_to_name?: string | null;
  due_date?: string | null;
  days_open?: number | null;
  cost_code_id?: string | null;
  drawing_reference?: string | null;
  lead_time_days?: number | null;
  review_notes?: string | null;
  reviewed_by?: string | null;
  reviewed_by_name?: string | null;
  reviewed_at?: string | null;
  revision_history: RevisionSummary[];
  comments_count: number;
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RevisionSummary {
  revision: number;
  formatted_number: string;
  status: string;
  created_at: string;
  reviewed_at?: string | null;
}

export interface SubmittalCreateInput {
  title: string;
  spec_section?: string;
  description?: string;
  submittal_type?: string;
  sub_company_id?: string;
  assigned_to?: string;
  due_date?: string;
  drawing_reference?: string;
  lead_time_days?: number;
}

export interface SubmittalUpdateInput {
  title?: string;
  spec_section?: string;
  description?: string;
  submittal_type?: string;
  assigned_to?: string;
  due_date?: string;
}
