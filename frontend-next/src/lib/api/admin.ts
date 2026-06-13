import { apiRequest } from "@/lib/api/client";
import type {
  AdminBotIntegration,
  AdminCompany,
  AdminConversation,
  AdminConversationMessage,
  AdminOverview,
  AdminProject,
  AdminStatusReasonPayload,
} from "@/lib/types/admin";

export function getAdminOverview() {
  return apiRequest<AdminOverview>("/admin/overview");
}

export function getAdminStats() {
  return apiRequest<AdminOverview>("/admin/stats");
}

export function listAdminCompanies() {
  return apiRequest<AdminCompany[]>("/admin/companies");
}

export function getAdminCompany(companyId: string | number) {
  return apiRequest<AdminCompany>(`/admin/companies/${companyId}`);
}

export function listAdminCompanyProjects(companyId: string | number) {
  return apiRequest<AdminProject[]>(`/admin/companies/${companyId}/projects`);
}

export function listAdminCompanyBotIntegrations(companyId: string | number) {
  return apiRequest<AdminBotIntegration[]>(`/admin/companies/${companyId}/bot-integrations`);
}

export function listAdminCompanyConversations(companyId: string | number) {
  return apiRequest<AdminConversation[]>(`/admin/companies/${companyId}/conversations`);
}

export function listAdminBotIntegrations() {
  return apiRequest<AdminBotIntegration[]>("/admin/bot-integrations");
}

export function listAdminConversations(params?: Record<string, string | number | boolean | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  });

  const suffix = search.toString() ? `?${search.toString()}` : "";
  return apiRequest<AdminConversation[]>(`/admin/conversations${suffix}`);
}

export function getAdminConversation(id: string | number) {
  return apiRequest<AdminConversation>(`/admin/conversations/${id}`);
}

export function getAdminConversationMessages(id: string | number) {
  return apiRequest<AdminConversationMessage[]>(`/admin/conversations/${id}/messages`);
}

export function activateCompany(companyId: string | number, payload?: AdminStatusReasonPayload) {
  return apiRequest<AdminCompany>(`/admin/companies/${companyId}/activate`, {
    method: "POST",
    body: JSON.stringify(payload || {}),
  });
}

export function suspendCompany(companyId: string | number, payload?: AdminStatusReasonPayload) {
  return apiRequest<AdminCompany>(`/admin/companies/${companyId}/suspend`, {
    method: "POST",
    body: JSON.stringify(payload || {}),
  });
}

export function blockCompany(companyId: string | number, payload?: AdminStatusReasonPayload) {
  return apiRequest<AdminCompany>(`/admin/companies/${companyId}/block`, {
    method: "POST",
    body: JSON.stringify(payload || {}),
  });
}

export function deleteCompany(companyId: string | number) {
  return apiRequest<void>(`/admin/users/${companyId}`, {
    method: "DELETE",
  });
}
