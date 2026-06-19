export type ProductRole = "company_admin" | "platform_owner" | string;

export interface LoginPayload {
  username: string;
  password: string;
}

export interface SignupPayload {
  username: string;
  password: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
  confirm_new_password: string;
}

export interface AuthTokenResponse {
  access_token: string | null;
}

export interface CurrentUser {
  id: number;
  username: string;
  role: ProductRole;
  roles?: string[];
  status?: string;
  company_name?: string | null;
  company_website?: string | null;
  created_at?: string;
}
