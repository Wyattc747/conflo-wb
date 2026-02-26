export interface PunchListItem {
  id: string;
  project_id: string;
  number: number;
  formatted_number: string;
  title: string;
  description?: string | null;
  location?: string | null;
  category: string;
  priority: string;
  status: string;
  assigned_to_sub_id?: string | null;
  assigned_to_sub_name?: string | null;
  assigned_to_user_id?: string | null;
  assigned_to_user_name?: string | null;
  due_date?: string | null;
  cost_code_id?: string | null;
  drawing_reference?: string | null;
  before_photo_ids: string[];
  after_photo_ids: string[];
  verification_photo_ids: string[];
  completion_notes?: string | null;
  completed_by?: string | null;
  completed_at?: string | null;
  verification_notes?: string | null;
  verified_by?: string | null;
  verified_at?: string | null;
  comments_count: number;
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PunchListItemCreateInput {
  title: string;
  description?: string;
  location?: string;
  category?: string;
  priority?: string;
  assigned_to_sub_id?: string;
  assigned_to_user_id?: string;
  due_date?: string;
  drawing_reference?: string;
}
