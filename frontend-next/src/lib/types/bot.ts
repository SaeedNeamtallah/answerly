export interface BotIntegration {
  id: number;
  owner_id: number;
  project_id: number;
  name: string;
  telegram_bot_id: string;
  telegram_username?: string | null;
  webhook_configured?: boolean;
  status: string;
  show_sources_to_customer?: boolean;
  human_handoff_enabled?: boolean;
  fallback_message?: string | null;
  last_error?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface BotIntegrationCreatePayload {
  project_id: number;
  name: string;
  bot_token: string;
  show_sources_to_customer?: boolean;
  human_handoff_enabled?: boolean;
  fallback_message?: string | null;
}

export interface BotIntegrationUpdatePayload {
  project_id?: number;
  name?: string;
  show_sources_to_customer?: boolean;
  human_handoff_enabled?: boolean;
  fallback_message?: string | null;
}

export interface RotateBotTokenPayload {
  bot_token: string;
}

export interface BotReadinessResponse {
  ready?: boolean;
  checks?: Record<string, unknown>;
  last_error?: string | null;
  status?: string;
}
