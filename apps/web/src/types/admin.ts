export interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: "admin" | "super_admin";
}

export interface PlatformStats {
  total_organizations: number;
  total_users: number;
  total_projects: number;
  total_sub_companies: number;
  monthly_recurring_revenue: number;
  orgs_by_tier: Record<string, number>;
}

export interface OrgListItem {
  id: string;
  name: string;
  subscription_tier: string | null;
  subscription_status: string | null;
  user_count: number;
  project_count: number;
  created_at: string | null;
}

export interface OrgDetail {
  id: string;
  name: string;
  subscription_tier: string | null;
  subscription_status: string | null;
  phone: string | null;
  timezone: string | null;
  created_at: string | null;
  users: OrgUser[];
  projects: OrgProject[];
}

export interface OrgUser {
  id: string;
  name: string;
  email: string;
  permission_level: string;
  status: string;
}

export interface OrgProject {
  id: string;
  name: string;
  phase: string;
  contract_value: number | null;
}

export interface UserSearchResult {
  id: string;
  name: string;
  email: string;
  user_type: "gc" | "sub" | "owner";
  organization_name: string | null;
  status: string;
}
