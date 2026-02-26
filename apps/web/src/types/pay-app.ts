export interface PayAppLineItem {
  budget_line_item_id: string | null;
  cost_code: string | null;
  description: string;
  scheduled_value: number;
  previous_applications: number;
  current_amount: number;
  materials_stored: number;
  total_completed: number;
  percent_complete: number;
  balance_to_finish: number;
  retainage: number;
}

export interface PayApp {
  id: string;
  project_id: string;
  number: number;
  formatted_number: string;
  pay_app_type: "SUB_TO_GC" | "GC_TO_OWNER";
  period_from: string;
  period_to: string;
  status: string;
  original_contract_sum: number;
  net_change_orders: number;
  contract_sum_to_date: number;
  total_completed_and_stored: number;
  retainage_percent: number;
  retainage_amount: number;
  total_earned_less_retainage: number;
  previous_certificates: number;
  current_payment_due: number;
  balance_to_finish: number;
  sub_company_id: string | null;
  sub_company_name: string | null;
  submitted_by_name: string | null;
  submitted_at: string | null;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  line_items: PayAppLineItem[];
  comments_count: number;
  created_at: string;
  updated_at: string;
}

export interface PayAppLineItemCreateInput {
  budget_line_item_id?: string;
  description: string;
  scheduled_value: number;
  previous_applications: number;
  current_amount: number;
  materials_stored: number;
}

export interface PayAppCreateInput {
  pay_app_type: "SUB_TO_GC" | "GC_TO_OWNER";
  period_from: string;
  period_to: string;
  retainage_percent: number;
  sub_company_id?: string;
  line_items: PayAppLineItemCreateInput[];
}
