import { clearAuthSession, readAccessToken } from "@/store/auth-store";

const DEFAULT_API_BASE_URL = "http://localhost:8000";
const BROWSER_API_BASE_URL = "/api";

export class ApiError extends Error {
  status: number;
  detail?: unknown;
  isUnavailable: boolean;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.isUnavailable = status === 0 || status >= 500;
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function getApiErrorMessage(error: unknown, fallback = "Request failed") {
  if (error instanceof ApiError) {
    return error.message || fallback;
  }

  if (error instanceof Error) {
    return error.message || fallback;
  }

  return fallback;
}

export function getApiBaseUrl() {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  const isBrowser = typeof window !== "undefined";

  if (isBrowser) {
    if (!url || /^https?:\/\/backend(?::|\/|$)/i.test(url)) {
      return BROWSER_API_BASE_URL;
    }
  }

  return (url || DEFAULT_API_BASE_URL).replace(/\/+$/, "");
}

export function getApiUrl(path: string) {
  return `${getApiBaseUrl()}${path}`;
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
    const response = await fetch(getApiUrl(path), {
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

      let message = typeof detail === "string" && detail.trim() ? detail : "";

      if (!message) {
        if (response.status >= 500) {
          message = `Backend Server Error (${response.status}): ${response.statusText || 'Internal Server Error'}`;
        } else {
          message = `Request failed (${response.status}): ${response.statusText || 'Unknown Error'}`;
        }
      } else {
         message = `${message} (${response.status})`;
      }
      throw new ApiError(response.status, message, payload);
    }

    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    throw new ApiError(0, `Network/Connection Error: ${errorMessage}`, error);
  }
}
