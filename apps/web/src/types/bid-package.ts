export interface BidSubmission {
  id: string;
  bid_package_id: string;
  sub_company_id: string;
  sub_company_name?: string | null;
  total_amount_cents: number;
  line_items: Record<string, unknown>[];
  qualifications?: string | null;
  schedule_duration_days?: number | null;
  exclusions?: string | null;
  inclusions?: string | null;
  notes?: string | null;
  status: string;
  submitted_at?: string | null;
  created_at: string;
}

export interface BidPackage {
  id: string;
  project_id: string;
  number: number;
  formatted_number: string;
  title: string;
  description?: string | null;
  trade?: string | null;
  trades: string[];
  status: string;
  bid_due_date?: string | null;
  pre_bid_meeting_date?: string | null;
  estimated_value_cents: number;
  requirements?: string | null;
  scope_documents: unknown[];
  invited_sub_ids: string[];
  submission_count: number;
  awarded_sub_id?: string | null;
  awarded_at?: string | null;
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BidPackageCreateInput {
  title: string;
  description?: string;
  trade?: string;
  trades?: string[];
  bid_due_date?: string;
  estimated_value_cents?: number;
  requirements?: string;
}

export interface BidPackageUpdateInput {
  title?: string;
  description?: string;
  trade?: string;
  trades?: string[];
  bid_due_date?: string;
  estimated_value_cents?: number;
  requirements?: string;
}

export interface BidSubmissionCreateInput {
  total_amount_cents?: number;
  line_items?: Record<string, unknown>[];
  qualifications?: string;
  schedule_duration_days?: number;
  exclusions?: string;
  inclusions?: string;
  notes?: string;
}

export interface BidComparisonResponse {
  submissions: BidSubmission[];
  lowest_amount_cents: number;
  highest_amount_cents: number;
  average_amount_cents: number;
  recommended_submission_id?: string | null;
}
