import { apiRequest } from "@/lib/api/client";
import type { QueryRequestPayload, QueryResponse } from "@/lib/types/query";

export function askProject(projectId: string | number, payload: QueryRequestPayload) {
  return apiRequest<QueryResponse>(`/projects/${projectId}/query`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
