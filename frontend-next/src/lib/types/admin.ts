export interface AdminOverview {
  companies?: number;
  projects?: number;
  bot_integrations?: number;
  conversations?: number;
  open_conversations?: number;
  escalated_conversations?: number;
  messages_last_24h?: number;
}

export interface AdminCompany {
  id: number;
  username: string;
  role: string;
  status: string;
  company_name?: string | null;
  project_count?: number;
  bot_count?: number;
  conversation_count?: number;
  created_at?: string;
}

export interface AdminProject {
  id: number;
  owner_id: number;
  name: string;
  description?: string | null;
  created_at?: string;
  updated_at?: string | null;
}

export interface AdminBotIntegration {
  id: number;
  owner_id: number;
  owner_username?: string | null;
  project_id: number;
  name: string;
  telegram_username?: string | null;
  status: string;
  last_error?: string | null;
  created_at?: string;
}

export interface AdminConversation {
  id: number;
  owner_id: number;
  bot_integration_id: number;
  project_id: number;
  status: string;
  needs_human: boolean;
  last_error?: string | null;
  last_message_at?: string | null;
  created_at?: string;
}

export interface AdminConversationMessage {
  id: number;
  owner_id: number;
  bot_integration_id: number;
  conversation_id: number;
  sender_type: string;
  text: string;
  answer_sources_json?: Array<Record<string, unknown>> | null;
  retrieval_metadata_json?: Record<string, unknown> | null;
  created_at?: string;
}

export interface AdminStatusReasonPayload {
  reason?: string;
  duration_minutes?: number;
}
