import { apiRequest } from "./client";
import type {
  SecurityEvent,
  SecuritySimulationResponse,
  SecurityStats,
  SecurityUserStatusEvent,
  SecurityUserStatusSummary,
} from "@/lib/types/security";

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
