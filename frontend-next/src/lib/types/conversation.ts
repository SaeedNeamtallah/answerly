export interface Conversation {
  id: number;
  owner_id: number;
  bot_integration_id: number;
  bot_name?: string | null;
  telegram_customer_id: number;
  customer_label: string;
  project_id: number;
  status: string;
  needs_human: boolean;
  assigned_to_user_id?: number | null;
  assigned_to_username?: string | null;
  last_message_at?: string | null;
  last_error?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ConversationMessage {
  id: number;
  conversation_id: number;
  sender_type: string;
  text: string;
  agent_user_id?: number | null;
  telegram_message_id?: string | null;
  answer_sources_json?: Array<Record<string, unknown>> | null;
  retrieval_metadata_json?: Record<string, unknown> | null;
  created_at?: string;
}

export interface ManualReplyPayload {
  text: string;
}
