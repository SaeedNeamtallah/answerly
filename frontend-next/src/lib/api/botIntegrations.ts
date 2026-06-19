import { apiRequest } from "@/lib/api/client";
import type {
  BotIntegration,
  BotIntegrationCreatePayload,
  BotIntegrationUpdatePayload,
  BotReadinessResponse,
  RotateBotTokenPayload,
} from "@/lib/types/bot";

export function listBotIntegrations() {
  return apiRequest<BotIntegration[]>("/bot-integrations");
}

export function createBotIntegration(payload: BotIntegrationCreatePayload) {
  return apiRequest<BotIntegration>("/bot-integrations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getBotIntegration(id: string | number) {
  return apiRequest<BotIntegration>(`/bot-integrations/${id}`);
}

export function updateBotIntegration(id: string | number, payload: BotIntegrationUpdatePayload) {
  return apiRequest<BotIntegration>(`/bot-integrations/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteBotIntegration(id: string | number) {
  return apiRequest<void>(`/bot-integrations/${id}`, {
    method: "DELETE",
  });
}

export function testBotIntegration(id: string | number) {
  return apiRequest<BotReadinessResponse>(`/bot-integrations/${id}/test`, {
    method: "POST",
  });
}

export function enableBotIntegration(id: string | number) {
  return apiRequest<BotIntegration>(`/bot-integrations/${id}/enable`, {
    method: "POST",
  });
}

export function disableBotIntegration(id: string | number) {
  return apiRequest<BotIntegration>(`/bot-integrations/${id}/disable`, {
    method: "POST",
  });
}

export function rotateBotToken(id: string | number, payload: RotateBotTokenPayload) {
  return apiRequest<BotIntegration>(`/bot-integrations/${id}/rotate-token`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getBotReadiness(id: string | number) {
  return apiRequest<BotReadinessResponse>(`/bot-integrations/${id}/readiness`);
}
