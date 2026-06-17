import { apiRequest } from './client';

export interface AdminRoleUser {
  id: number;
  username: string;
  email: string | null;
  role: string;
}

export interface UpdateRoleResponse {
  success: boolean;
  user_id: number;
  new_role: string;
  message: string;
}

export const adminRolesApi = {
  listUsers: () => 
    apiRequest<AdminRoleUser[]>('/admin/roles/users'),
    
  updateUserRole: (userId: number, role: string, reason: string) => 
    apiRequest<UpdateRoleResponse>(`/admin/roles/users/${userId}`, {
      method: 'POST',
      body: JSON.stringify({ role, reason }),
    }),
};
