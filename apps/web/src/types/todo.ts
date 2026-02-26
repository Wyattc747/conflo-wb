export interface Todo {
  id: string;
  project_id: string;
  title: string;
  description?: string | null;
  status: string;
  priority: string;
  assigned_to?: string | null;
  assigned_to_name?: string | null;
  due_date?: string | null;
  category?: string | null;
  cost_code_id?: string | null;
  source_type?: string | null;
  source_id?: string | null;
  completed_at?: string | null;
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TodoCreateInput {
  title: string;
  description?: string;
  assigned_to?: string;
  due_date?: string;
  priority?: string;
  category?: string;
}

export interface TodoUpdateInput {
  title?: string;
  description?: string;
  assigned_to?: string;
  due_date?: string;
  priority?: string;
  category?: string;
}
