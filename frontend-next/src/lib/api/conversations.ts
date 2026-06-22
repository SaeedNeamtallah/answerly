import { apiRequest } from "@/lib/api/client";
import type {
  Conversation,
  ConversationMessage,
  ManualReplyPayload,
} from "@/lib/types/conversation";

export function listConversations(params?: Record<string, string | number | boolean | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  });

  const suffix = search.toString() ? `?${search.toString()}` : "";
  return apiRequest<Conversation[]>(`/conversations${suffix}`);
}

export function getConversation(id: string | number) {
  return apiRequest<Conversation>(`/conversations/${id}`);
}

export function getConversationMessages(id: string | number) {
  return apiRequest<ConversationMessage[]>(`/conversations/${id}/messages`);
}

export function replyToConversation(id: string | number, payload: ManualReplyPayload) {
  return apiRequest<ConversationMessage>(`/conversations/${id}/reply`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resolveConversation(id: string | number) {
  return apiRequest<Conversation>(`/conversations/${id}/resolve`, {
    method: "POST",
  });
}

export function escalateConversation(id: string | number) {
  return apiRequest<Conversation>(`/conversations/${id}/escalate`, {
    method: "POST",
  });
}

export function assignConversation(id: string | number) {
  return apiRequest<Conversation>(`/conversations/${id}/assign`, {
    method: "POST",
  });
}

export function blockCustomer(id: string | number) {
  return apiRequest<Conversation>(`/conversations/${id}/block-customer`, {
    method: "POST",
  });
}
