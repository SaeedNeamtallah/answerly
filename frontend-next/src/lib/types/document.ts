export interface DocumentAsset {
  id: number;
  project_id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  status: string;
  error_message?: string | null;
  created_at?: string;
  processed_at?: string | null;
  extra_metadata?: Record<string, unknown>;
}

export interface TaskStatusResponse {
  task_id: string;
  status: string;
  asset_id?: number;
  project_id?: number;
  result?: unknown;
  meta?: Record<string, unknown>;
  error?: string;
}
