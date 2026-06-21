import { apiRequest } from './client';

export interface WhatsAppIntegration {
  id: number;
  owner_id: number;
  project_id: number;
  name: string;
  phone_number?: string;
  session_id: string;
  status: string;
  show_sources_to_customer: boolean;
  human_handoff_enabled: boolean;
  fallback_message?: string;
  system_prompt?: string;
  last_error?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateWhatsAppIntegrationRequest {
  project_id: number;
  name: string;
  phone_number?: string;
  show_sources_to_customer?: boolean;
  human_handoff_enabled?: boolean;
  fallback_message?: string;
  system_prompt?: string;
}

export interface UpdateWhatsAppIntegrationRequest {
  project_id?: number;
  name?: string;
  show_sources_to_customer?: boolean;
  human_handoff_enabled?: boolean;
  fallback_message?: string;
  system_prompt?: string;
}

export interface SessionStatus {
  status: 'initializing' | 'qr_ready' | 'connected' | 'disconnected' | 'expired' | 'error' | 'pending' | 'not_found' | 'unknown';
  qr?: string;
  last_error?: string | null;
}

export const getWhatsAppIntegrations = async (): Promise<WhatsAppIntegration[]> => {
  return apiRequest('/whatsapp-integrations');
};

export const createWhatsAppIntegration = async (data: CreateWhatsAppIntegrationRequest): Promise<WhatsAppIntegration> => {
  return apiRequest('/whatsapp-integrations', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const getWhatsAppIntegration = async (id: number): Promise<WhatsAppIntegration> => {
  return apiRequest(`/whatsapp-integrations/${id}`);
};

export const updateWhatsAppIntegration = async (
  id: number,
  data: UpdateWhatsAppIntegrationRequest
): Promise<WhatsAppIntegration> => {
  return apiRequest(`/whatsapp-integrations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
};

export const deleteWhatsAppIntegration = async (id: number): Promise<void> => {
  return apiRequest(`/whatsapp-integrations/${id}`, {
    method: 'DELETE',
  });
};

export const connectWhatsAppSession = async (id: number): Promise<{ success: boolean }> => {
  return apiRequest(`/whatsapp-integrations/${id}/connect`, {
    method: 'POST',
  });
};

export const getWhatsAppSessionStatus = async (id: number): Promise<SessionStatus> => {
  return apiRequest(`/whatsapp-integrations/${id}/session-status`);
};
