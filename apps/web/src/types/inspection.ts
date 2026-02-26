export interface InspectionTemplate {
  id: string;
  organization_id: string;
  name: string;
  description?: string | null;
  category: string;
  checklist_items: ChecklistItem[];
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChecklistItem {
  label: string;
  required: boolean;
  order: number;
}

export interface Inspection {
  id: string;
  project_id: string;
  number: number;
  formatted_number: string;
  title: string;
  template_id?: string | null;
  template_name?: string | null;
  category: string;
  scheduled_date?: string | null;
  scheduled_time?: string | null;
  location?: string | null;
  inspector_name?: string | null;
  inspector_company?: string | null;
  status: string;
  overall_result?: string | null;
  checklist_results: ChecklistResult[];
  photo_ids: string[];
  notes?: string | null;
  comments_count: number;
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
  completed_at?: string | null;
  updated_at: string;
}

export interface ChecklistResult {
  item_label: string;
  result: string;
  notes?: string | null;
}

export interface InspectionCreateInput {
  template_id?: string;
  title?: string;
  category?: string;
  scheduled_date?: string;
  scheduled_time?: string;
  location?: string;
  inspector_name?: string;
  inspector_company?: string;
  notes?: string;
}
