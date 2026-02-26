export interface ProcurementItem {
  id: string;
  project_id: string;
  item_name: string;
  description?: string | null;
  status: string;
  category?: string | null;
  spec_section?: string | null;
  quantity?: number | null;
  unit?: string | null;
  vendor?: string | null;
  vendor_contact?: string | null;
  vendor_phone?: string | null;
  vendor_email?: string | null;
  estimated_cost_cents: number;
  actual_cost_cents: number;
  po_number?: string | null;
  lead_time_days?: number | null;
  required_on_site_date?: string | null;
  order_by_date?: string | null;
  expected_delivery_date?: string | null;
  actual_delivery_date?: string | null;
  tracking_number?: string | null;
  is_at_risk: boolean;
  assigned_to?: string | null;
  sub_company_id?: string | null;
  linked_schedule_task_id?: string | null;
  notes?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProcurementCreateInput {
  item_name: string;
  description?: string;
  category?: string;
  vendor?: string;
  estimated_cost_cents?: number;
  lead_time_days?: number;
  required_on_site_date?: string;
}

export interface ProcurementUpdateInput {
  item_name?: string;
  description?: string;
  category?: string;
  vendor?: string;
  estimated_cost_cents?: number;
  actual_cost_cents?: number;
  po_number?: string;
  lead_time_days?: number;
  tracking_number?: string;
  notes?: string;
}
