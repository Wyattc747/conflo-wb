export interface SubPricing {
  sub_company_id: string;
  sub_company_name: string | null;
  amount: number | null;
  description: string | null;
  schedule_impact_days: number;
  status: string;
  submitted_at: string | null;
}

export interface ChangeOrder {
  id: string;
  project_id: string;
  number: number;
  formatted_number: string;
  title: string;
  description: string | null;
  reason: string | null;
  status: string;
  order_type: string | null;
  cost_code_id: string | null;
  cost_code: string | null;
  amount: number; // cents
  markup_percent: number | null;
  markup_amount: number; // cents
  gc_amount: number; // cents
  schedule_impact_days: number;
  sub_pricings: SubPricing[];
  created_by: string;
  created_by_name: string | null;
  submitted_to_owner_at: string | null;
  owner_decision: string | null;
  owner_decision_by: string | null;
  owner_decision_at: string | null;
  owner_decision_notes: string | null;
  priority: string;
  drawing_reference: string | null;
  spec_section: string | null;
  comments_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChangeOrderCreateInput {
  title: string;
  description?: string;
  reason?: string;
  amount: number; // cents
  cost_code_id?: string;
  schedule_impact_days?: number;
  priority?: string;
  drawing_reference?: string;
  spec_section?: string;
  sub_company_ids?: string[];
}

export interface ChangeOrderUpdateInput {
  title?: string;
  description?: string;
  reason?: string;
  amount?: number;
  gc_amount?: number;
  markup_percent?: number;
  cost_code_id?: string;
  schedule_impact_days?: number;
  priority?: string;
  drawing_reference?: string;
  spec_section?: string;
}
