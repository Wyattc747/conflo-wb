export interface Photo {
  id: string;
  project_id?: string | null;
  file_id?: string | null;
  linked_type?: string | null;
  linked_id?: string | null;
  caption?: string | null;
  tags: string[];
  location?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  uploaded_by?: string | null;
  uploaded_by_name?: string | null;
  captured_at?: string | null;
  created_at: string;
}

export interface PhotoCreateInput {
  file_id?: string;
  linked_type?: string;
  linked_id?: string;
  caption?: string;
  tags?: string[];
  location?: string;
}

export interface PhotoUpdateInput {
  caption?: string;
  tags?: string[];
  location?: string;
}
