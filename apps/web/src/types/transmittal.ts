export interface Transmittal {
  id: string;
  project_id: string;
  number: number;
  formatted_number: string;
  subject: string;
  to_company?: string | null;
  to_contact?: string | null;
  from_company?: string | null;
  from_contact?: string | null;
  purpose: string;
  description?: string | null;
  status: string;
  items: TransmittalItem[];
  sent_via: string;
  sent_at?: string | null;
  received_at?: string | null;
  due_date?: string | null;
  comments_count: number;
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TransmittalItem {
  description: string;
  quantity: number;
  document_type?: string | null;
}

export interface TransmittalCreateInput {
  subject: string;
  to_company?: string;
  to_contact?: string;
  from_company?: string;
  from_contact?: string;
  purpose?: string;
  description?: string;
  items?: TransmittalItem[];
  due_date?: string;
  sent_via?: string;
}
