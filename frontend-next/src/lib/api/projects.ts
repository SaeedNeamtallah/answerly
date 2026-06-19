import { apiRequest } from "@/lib/api/client";
import type { ApiListResponse } from "@/lib/types/common";
import type {
  Project,
  ProjectCreatePayload,
  ProjectStats,
  ProjectUpdatePayload,
} from "@/lib/types/project";

export function normalizeProjectListResponse(payload: ApiListResponse<Project> | Project[]) {
  if (Array.isArray(payload)) {
    return payload;
  }

  return payload.items || payload.data || payload.results || [];
}

export function listProjects() {
  return apiRequest<ApiListResponse<Project>>("/projects");
}

export function createProject(payload: ProjectCreatePayload) {
  return apiRequest<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getProject(id: string | number) {
  return apiRequest<Project>(`/projects/${id}`);
}

export function updateProject(id: string | number, payload: ProjectUpdatePayload) {
  return apiRequest<Project>(`/projects/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteProject(id: string | number) {
  return apiRequest<void>(`/projects/${id}`, {
    method: "DELETE",
  });
}

export function getProjectStats(id: string | number) {
  return apiRequest<ProjectStats>(`/projects/${id}/stats`);
}

export function reindexProject(id: string | number, do_reset = false) {
  return apiRequest<{ task_id: string; status: string; project_id: number }>(`/projects/${id}/index`, {
    method: "POST",
    body: JSON.stringify({ do_reset }),
  });
}
