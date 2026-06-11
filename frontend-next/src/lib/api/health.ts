import { apiRequest } from "@/lib/api/client";
import type { HealthResponse } from "@/lib/types/common";

export function getHealth() {
  return apiRequest<HealthResponse>("/health", { auth: false });
}

export function getLiveHealth() {
  return apiRequest<unknown>("/health/live", { auth: false });
}
