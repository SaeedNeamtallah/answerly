'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { adminRolesApi, AdminRoleUser } from '@/lib/api/admin-roles';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuthStore } from '@/store/auth-store';
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from '@/components/ui/empty';
import { Shield } from 'lucide-react';

const AVAILABLE_ROLES = [
  'platform_owner',
  'company_admin',
  'security_engineer',
  'cybersecurity_engineer',
  'admin',
  'user',
];

export function RoleManagement() {
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((state) => state.currentUser);
  const [selectedUser, setSelectedUser] = useState<AdminRoleUser | null>(null);
  const [newRole, setNewRole] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const { data: users, isLoading, error } = useQuery({
    queryKey: ['admin-roles-users'],
    queryFn: adminRolesApi.listUsers,
  });

  const updateRoleMutation = useMutation({
    mutationFn: (data: { userId: number; role: string; reason: string }) =>
      adminRolesApi.updateUserRole(data.userId, data.role, data.reason),
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ['admin-roles-users'] });
      setIsDialogOpen(false);
      setSelectedUser(null);
      setNewRole('');
      setReason('');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to update role');
    },
  });

  const handleRoleChange = (user: AdminRoleUser, role: string) => {
    if (user.role === role) return;
    setSelectedUser(user);
    setNewRole(role);
    setReason('');
    setIsDialogOpen(true);
  };

  const handleConfirm = () => {
    if (!selectedUser || !newRole || reason.length < 3) return;
    updateRoleMutation.mutate({
      userId: selectedUser.id,
      role: newRole,
      reason,
    });
  };

  if (isLoading) {
    return <div className="p-8 text-center text-muted-foreground">Loading users...</div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-destructive">
        Error loading users: {(error as Error).message}
      </div>
    );
  }

  if (!users || users.length === 0) {
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Shield />
          </EmptyMedia>
          <EmptyTitle>No Users Found</EmptyTitle>
          <EmptyDescription>There are no users available to manage roles.</EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Username</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Current Role</TableHead>
              <TableHead>Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>{user.id}</TableCell>
                <TableCell className="font-medium">{user.username}</TableCell>
                <TableCell>{user.email || '—'}</TableCell>
                <TableCell>
                  <span className="inline-flex items-center rounded-md bg-secondary px-2 py-1 text-xs font-medium">
                    {user.role}
                  </span>
                </TableCell>
                <TableCell>
                  <Select
                    disabled={user.id === currentUser?.id}
                    value={user.role}
                    onValueChange={(value) => handleRoleChange(user, value)}
                  >
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent>
                      {AVAILABLE_ROLES.map((role) => (
                        <SelectItem key={role} value={role}>
                          {role}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Role Change</DialogTitle>
            <DialogDescription>
              You are about to change the role for <strong>{selectedUser?.username}</strong> from{' '}
              <strong>{selectedUser?.role}</strong> to <strong>{newRole}</strong>.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="reason">Reason for Change (Required)</Label>
              <Input
                id="reason"
                placeholder="e.g., Promotion to Security Team"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                minLength={3}
              />
              {reason.length > 0 && reason.length < 3 && (
                <p className="text-xs text-destructive">Reason must be at least 3 characters.</p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirm}
              disabled={reason.length < 3 || updateRoleMutation.isPending}
            >
              {updateRoleMutation.isPending ? 'Updating...' : 'Confirm Change'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
