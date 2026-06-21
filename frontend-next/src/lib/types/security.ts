export interface SecurityEvent {
  id: number;
  timestamp: string;
  event_type: string;
  severity: string;
  user_id?: number | null;
  username?: string | null;
  message: string;
  ip_address?: string | null;
  is_simulation: boolean;
  metadata?: Record<string, unknown>;
}

export interface SecurityEventPage {
  items: SecurityEvent[];
  total: number;
  page: number;
  size: number;
}

export interface SecurityStats {
  total_events: number;
  login_failures: number;
  brute_force_attempts: number;
  blocked_uploads: number;
}

export interface Incident {
  id: number;
  incident_type: string;
  severity: string;
  status: string;
  is_false_positive: boolean;
  actor_user_id?: number | null;
  actor_username?: string | null;
  actor_ip?: string | null;
  investigation_notes?: string | null;
  assigned_to_id?: number | null;
  assigned_to_username?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SecuritySimulationResponse {
  generated_count: number;
  escalation_applied: boolean;
  escalation_result: string;
  target_user_id: number | null;
  stats: SecurityStats;
  events: SecurityEvent[];
}

export interface SecurityUserStatusSummary {
  total_active: number;
  total_suspended: number;
  total_blocked: number;
}

export interface SecurityUserStatusEvent {
  id: number;
  timestamp: string;
  event_type: string;
  user_id: number | null;
  actor: string | null;
  reason: string | null;
  metadata: Record<string, unknown>;
  is_simulation: boolean;
  delivery_status: string;
}
