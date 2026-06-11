import { apiRequest } from "@/lib/api/client";
import type { ProviderConfigResponse, ProviderConfigUpdatePayload } from "@/lib/types/config";

export function getProviders() {
  return apiRequest<ProviderConfigResponse>("/config/providers");
}

export function updateProviders(payload: ProviderConfigUpdatePayload) {
  return apiRequest<ProviderConfigResponse>("/config/providers", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
