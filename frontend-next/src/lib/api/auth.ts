import { apiRequest } from "@/lib/api/client";
import type {
  AuthTokenResponse,
  ChangePasswordPayload,
  CurrentUser,
  LoginPayload,
  SignupPayload,
} from "@/lib/types/auth";
import type { ApiMessageResponse } from "@/lib/types/common";

export function login(payload: LoginPayload) {
  return apiRequest<AuthTokenResponse>("/auth/login", {
    method: "POST",
    auth: false,
    body: JSON.stringify(payload),
  });
}

export function signup(payload: SignupPayload) {
  return apiRequest<ApiMessageResponse>("/auth/signup", {
    method: "POST",
    auth: false,
    body: JSON.stringify(payload),
  });
}

export function getMe() {
  return apiRequest<CurrentUser>("/auth/me");
}

export function changePassword(payload: ChangePasswordPayload) {
  return apiRequest<ApiMessageResponse>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function googleLogin(token: string) {
  return apiRequest<AuthTokenResponse>("/auth/google/login", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ token }),
  });
}

export function forgotPassword(email: string) {
  return apiRequest<ApiMessageResponse>("/auth/forgot-password", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(payload: { token: string; new_password: string }) {
  return apiRequest<ApiMessageResponse>("/auth/reset-password", {
    method: "POST",
    auth: false,
    body: JSON.stringify(payload),
  });
}
