export interface Comment {
  id: string;
  commentable_type: string;
  commentable_id: string;
  body: string;
  author_type: string;
  author_id: string;
  author_name?: string | null;
  is_official_response: boolean;
  mentions: string[];
  attachments: string[];
  created_at: string;
  updated_at: string;
}
