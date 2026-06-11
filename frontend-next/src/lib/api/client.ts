import { clearAuthSession, readAccessToken } from "@/store/auth-store";

const DEFAULT_API_BASE_URL = "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail?: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function getApiBaseUrl() {
  return (process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/+$/, "");
}

function redirectToLogin() {
  if (typeof window === "undefined") {
    return;
  }

  window.location.replace("/login?reason=expired");
}

export async function apiRequest<T>(
  path: string,
  options: (RequestInit & { auth?: boolean }) = {},
): Promise<T> {
  const { auth = true, headers, body, ...rest } = options;
  const finalHeaders = new Headers(headers || {});

  if (auth) {
    const token = readAccessToken();
    if (token) {
      finalHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  if (body && !(body instanceof FormData) && !finalHeaders.has("Content-Type")) {
    finalHeaders.set("Content-Type", "application/json");
  }

  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...rest,
      headers: finalHeaders,
      body,
    });

    if (response.status === 204) {
      return undefined as T;
    }

    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
      ? await response.json()
      : await response.text();

    if (response.status === 401) {
      clearAuthSession();
      redirectToLogin();
      throw new ApiError(401, "Unauthorized", payload);
    }

    if (response.status === 403) {
      throw new ApiError(403, "Forbidden", payload);
    }

    if (!response.ok) {
      const detail =
        typeof payload === "object" && payload && "detail" in payload
          ? (payload as { detail?: string }).detail
          : undefined;
      throw new ApiError(response.status, detail || response.statusText || "Request failed", payload);
    }

    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw new ApiError(0, "Backend unavailable", error);
  }
}
