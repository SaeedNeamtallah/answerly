import { apiRequest } from "./client";

export interface SecurityStats {
  total_events: number;
  login_failures: number;
  brute_force_attempts: number;
  blocked_uploads: number;
}

export interface SecurityEvent {
  id: number;
  timestamp: string;
  event_type: string;
  severity: string;
  user_id: number | null;
  username: string | null;
  ip_address: string | null;
  message: string;
  metadata: Record<string, any>;
  is_simulation: boolean;
  delivery_status: string;
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
  metadata: Record<string, any>;
  is_simulation: boolean;
  delivery_status: string;
}

export const securityApi = {
  getStats: () => {
    return apiRequest<SecurityStats>("/security/stats");
  },

  getEvents: (limit: number = 20) => {
    return apiRequest<SecurityEvent[]>(`/security/events?limit=${limit}`);
  },

  getUserStatusSummary: () => {
    return apiRequest<SecurityUserStatusSummary>("/security/users/status-summary");
  },

  getUserStatusEvents: (limit: number = 20) => {
    return apiRequest<SecurityUserStatusEvent[]>(`/security/users/events?limit=${limit}`);
  },

  simulateAttack: (targetUserId?: number, escalateToBlock: boolean = false) => {
    const params = new URLSearchParams();
    if (targetUserId) params.append("target_user_id", targetUserId.toString());
    if (escalateToBlock) params.append("escalate_to_block", "true");

    const query = params.toString();
    const url = query ? `/security/simulate?${query}` : "/security/simulate";

    return apiRequest<SecuritySimulationResponse>(url, {
      method: "POST",
    });
  },

  // Note: /security/events/export is best handled directly via window.open() or an anchor tag
  // Note: /security/events/stream is best handled via EventSource or fetch-event-source
};
