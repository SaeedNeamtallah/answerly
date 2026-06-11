import { apiRequest } from "@/lib/api/client";
import type { DocumentAsset, TaskStatusResponse } from "@/lib/types/document";

export function listDocuments(projectId: string | number) {
  return apiRequest<DocumentAsset[]>(`/projects/${projectId}/documents`);
}

export function uploadDocument(projectId: string | number, file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<DocumentAsset>(`/projects/${projectId}/documents`, {
    method: "POST",
    body: formData,
  });
}

export function processDocument(assetId: string | number) {
  return apiRequest<TaskStatusResponse>(`/documents/${assetId}/process`, {
    method: "POST",
  });
}

export function processAndIndexDocument(assetId: string | number, do_reset = false) {
  return apiRequest<TaskStatusResponse>(`/documents/${assetId}/process-and-index`, {
    method: "POST",
    body: JSON.stringify({ do_reset }),
  });
}

export function deleteDocument(assetId: string | number) {
  return apiRequest<void>(`/documents/${assetId}`, {
    method: "DELETE",
  });
}

export function getTask(taskId: string) {
  return apiRequest<TaskStatusResponse>(`/tasks/${taskId}`);
}
