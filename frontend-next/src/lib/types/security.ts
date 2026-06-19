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
  metadata?: Record<string, any>;
}

export interface SecurityEventPage {
  items: SecurityEvent[];
  total: number;
  page: number;
  size: number;
}

export interface SecurityStats {
  total_events: number;
  active_incidents: number;
  simulations_run: number;
  events_by_severity: Record<string, number>;
  events_by_type: Record<string, number>;
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

export interface AttackSimulationResponse {
  success: boolean;
  simulation_id: string;
  events_generated: number;
  message: string;
}
