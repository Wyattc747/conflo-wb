export interface DrawingSheet {
  id: string;
  drawing_id: string;
  sheet_number: string;
  title?: string | null;
  description?: string | null;
  revision: string;
  revision_date?: string | null;
  is_current: boolean;
  file_id?: string | null;
  uploaded_by?: string | null;
  created_at: string;
}

export interface DrawingSet {
  id: string;
  project_id: string;
  set_number: string;
  title: string;
  discipline?: string | null;
  description?: string | null;
  received_from?: string | null;
  is_current_set: boolean;
  sheet_count: number;
  sheets: DrawingSheet[];
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DrawingSetCreateInput {
  set_number: string;
  title: string;
  discipline?: string;
  description?: string;
  received_from?: string;
}

export interface DrawingSetUpdateInput {
  set_number?: string;
  title?: string;
  discipline?: string;
  description?: string;
  received_from?: string;
}
