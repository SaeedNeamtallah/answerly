import { Metadata } from 'next';
import { RoleManagement } from '@/components/admin/RoleManagement';

export const metadata: Metadata = {
  title: 'Role Management',
  description: 'Manage user roles and permissions.',
};

export default function RolesPage() {
  return (
    <div className="flex flex-col gap-6 p-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Role Management</h1>
        <p className="text-muted-foreground">
          Assign and modify roles for users across the platform.
        </p>
      </div>
      
      <RoleManagement />
    </div>
  );
}
