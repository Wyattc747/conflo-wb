export interface ScheduleTask {
  id: string;
  project_id: string;
  name: string;
  description?: string | null;
  wbs_code?: string | null;
  parent_task_id?: string | null;
  sort_order: number;
  start_date?: string | null;
  end_date?: string | null;
  duration?: number | null;
  baseline_start?: string | null;
  baseline_end?: string | null;
  baseline_duration?: number | null;
  owner_start_date?: string | null;
  owner_end_date?: string | null;
  sub_start_date?: string | null;
  sub_end_date?: string | null;
  percent_complete: number;
  actual_start?: string | null;
  actual_end?: string | null;
  assigned_to?: string | null;
  assigned_to_sub_id?: string | null;
  milestone: boolean;
  is_critical: boolean;
  cost_code_id?: string | null;
  dependencies: TaskDependency[];
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskDependency {
  id: string;
  predecessor_id: string;
  dependency_type: string;
  lag_days: number;
}

export interface ScheduleDelay {
  id: string;
  project_id: string;
  task_ids: string[];
  delay_days: number;
  reason_category: string;
  responsible_party: string;
  description: string;
  impacts_gc_schedule: boolean;
  impacts_owner_schedule: boolean;
  impacts_sub_schedule: boolean;
  daily_log_id?: string | null;
  rfi_id?: string | null;
  change_order_id?: string | null;
  status: string;
  approved_by?: string | null;
  approved_at?: string | null;
  applied_at?: string | null;
  created_by: string;
  created_at: string;
}

export interface ScheduleVersion {
  id: string;
  project_id: string;
  version_type: string;
  version_number: number;
  title: string;
  notes?: string | null;
  snapshot_data: Record<string, unknown>;
  published_by: string;
  published_at: string;
}

export interface ScheduleConfig {
  id?: string;
  project_id: string;
  schedule_mode: string;
  derivation_method: string;
  owner_buffer_percent?: number | null;
  sub_compress_percent?: number | null;
  health_on_track_max_days: number;
  health_at_risk_max_days: number;
  sub_notify_intervals: number[];
}

export interface ScheduleHealth {
  status: string;
  slippage_days: number;
  on_track_threshold: number;
  at_risk_threshold: number;
}

export interface ScheduleTaskCreateInput {
  name: string;
  description?: string;
  wbs_code?: string;
  parent_task_id?: string;
  start_date?: string;
  end_date?: string;
  duration?: number;
  assigned_to?: string;
  assigned_to_sub_id?: string;
  milestone?: boolean;
  is_critical?: boolean;
}
