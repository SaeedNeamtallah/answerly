export interface Project {
  id: number;
  name: string;
  description?: string | null;
  extra_metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string | null;
}

export interface ProjectStats {
  project?: Project;
  stats?: Record<string, unknown>;
}

export interface ProjectCreatePayload {
  name: string;
  description?: string;
  metadata?: Record<string, unknown>;
}

export interface ProjectUpdatePayload {
  name?: string;
  description?: string;
  metadata?: Record<string, unknown>;
}
