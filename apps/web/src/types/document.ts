export interface DocumentFolder {
  id: string;
  project_id: string;
  name: string;
  parent_folder_id?: string | null;
  is_system: boolean;
  created_at: string;
}

export interface Document {
  id: string;
  project_id: string;
  title: string;
  description?: string | null;
  category?: string | null;
  folder_id?: string | null;
  folder_name?: string | null;
  file_id?: string | null;
  tags: string[];
  version: number;
  uploaded_by?: string | null;
  uploaded_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentCreateInput {
  title: string;
  description?: string;
  category?: string;
  folder_id?: string;
  file_id?: string;
  tags?: string[];
}

export interface DocumentUpdateInput {
  title?: string;
  description?: string;
  category?: string;
  folder_id?: string;
  tags?: string[];
}
