export interface BudgetLineItem {
  id: string;
  project_id: string;
  cost_code: string;
  description: string | null;
  original_amount: number; // cents
  approved_changes: number; // cents
  revised_amount: number; // cents
  billed_to_date: number; // cents
  remaining: number; // cents
  percent_complete: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface BudgetSummary {
  original_contract: number; // cents
  approved_changes: number; // cents
  revised_contract: number; // cents
  billed_to_date: number; // cents
  remaining: number; // cents
  percent_complete: number;
  line_items: BudgetLineItem[];
  change_orders_pending: number;
  change_orders_pending_amount: number; // cents
}

export interface BudgetLineItemCreateInput {
  cost_code: string;
  description: string;
  original_amount: number; // cents
  notes?: string;
}

export interface BudgetLineItemUpdateInput {
  description?: string;
  original_amount?: number; // cents
  notes?: string;
}
