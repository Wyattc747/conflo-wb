export interface DailyLog {
  id: string;
  project_id: string;
  log_date: string;
  number: string;
  weather_data?: {
    condition?: string;
    temp_high?: number;
    temp_low?: number;
    precipitation?: number;
    wind_speed?: number;
    humidity?: number;
    summary?: string;
  } | null;
  summary?: string | null;
  work_performed?: string | null;
  materials_received?: string | null;
  equipment_on_site?: string | null;
  visitors?: { name: string; company: string }[] | null;
  safety_incidents?: string | null;
  delays_text?: string | null;
  extra_work?: string | null;
  manpower?: { trade: string; workers: number; hours: number }[] | null;
  status: string;
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DailyLogCreateInput {
  log_date: string;
  weather_condition?: string;
  temp_high?: number;
  temp_low?: number;
  precipitation?: number;
  wind_speed?: number;
  humidity?: number;
  summary?: string;
  work_performed?: string;
  delays?: string;
  manpower?: { trade: string; workers: number; hours: number }[];
  status?: string;
}

export interface DailyLogUpdateInput {
  weather_condition?: string;
  temp_high?: number;
  temp_low?: number;
  work_performed?: string;
  delays?: string;
  manpower?: { trade: string; workers: number; hours: number }[];
}
