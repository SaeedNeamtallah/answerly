import { apiRequest } from "./client";
import type { Incident, SecurityEvent } from "@/lib/types/security";

export interface IncidentDetails extends Incident {
  events: SecurityEvent[];
}

export const incidentsApi = {
  getIncidents: (params?: { status?: string; severity?: string; false_positive?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append("status", params.status);
    if (params?.severity) searchParams.append("severity", params.severity);
    if (params?.false_positive !== undefined) searchParams.append("false_positive", params.false_positive.toString());

    const queryStr = searchParams.toString();
    return apiRequest<Incident[]>(`/incidents${queryStr ? `?${queryStr}` : ""}`);
  },

  getIncidentDetails: (id: number) =>
    apiRequest<IncidentDetails>(`/incidents/${id}`),

  assignIncident: (id: number) =>
    apiRequest<Incident>(`/incidents/${id}/assign`, { method: "POST" }),

  updateNotes: (id: number, notes: string) =>
    apiRequest<Incident>(`/incidents/${id}/notes`, {
      method: "PATCH",
      body: JSON.stringify({ notes }),
    }),

  updateStatus: (id: number, status: string) =>
    apiRequest<Incident>(`/incidents/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  markFalsePositive: (id: number, is_false_positive: boolean) =>
    apiRequest<Incident>(`/incidents/${id}/false-positive`, {
      method: "PATCH",
      body: JSON.stringify({ is_false_positive }),
    }),

  reopenIncident: (id: number) =>
    apiRequest<Incident>(`/incidents/${id}/reopen`, { method: "POST" }),

  takeAction: (id: number, action_type: string, metadata?: Record<string, any>) =>
    apiRequest<Incident>(`/incidents/${id}/action`, {
      method: "POST",
      body: JSON.stringify({ action_type, metadata }),
    }),
};
