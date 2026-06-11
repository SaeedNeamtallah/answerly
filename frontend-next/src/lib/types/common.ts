export type ApiId = number | string;

export interface ApiListResponse<T> {
  items?: T[];
  data?: T[];
  results?: T[];
  total?: number;
  total_count?: number;
}

export interface ApiMessageResponse {
  message?: string;
  detail?: string;
}

export interface HealthResponse {
  status?: string;
  checks?: Record<string, unknown>;
  details?: Record<string, unknown>;
}

export type AsyncState = "idle" | "loading" | "success" | "error";
