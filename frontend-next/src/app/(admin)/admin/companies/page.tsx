"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { activateCompany, blockCompany, deleteCompany, listAdminCompanies, suspendCompany } from "@/lib/api/admin";

import { CompaniesTable } from "@/components/admin/CompaniesTable";
import { PageHeader } from "@/components/layout/PageHeader";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { Button } from "@/components/ui/button";

export default function AdminCompaniesPage() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["adminCompanies"], queryFn: listAdminCompanies });
  const mutation = useMutation({
    mutationFn: async ({ id, action }: { id: number; action: "activate" | "suspend" | "block" }) => {
      if (action === "activate") return activateCompany(id, {});
      if (action === "suspend") return suspendCompany(id, { reason: "platform_owner_suspension" });
      return blockCompany(id, { reason: "platform_owner_block" });
    },
    onSuccess: () => {
      toast.success("Company status updated");
      queryClient.invalidateQueries({ queryKey: ["adminCompanies"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteCompany(id),
    onSuccess: () => {
      toast.success("Company and associated employees deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["adminCompanies"] });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to delete company");
    },
  });

  if (query.isLoading) {
    return <LoadingState label="Loading companies..." />;
  }

  if (query.isError) {
    return <ErrorState description="Failed to load companies." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Admin" title="Companies" description="Platform-owner account actions use confirm dialogs instead of browser prompts." />
      <CompaniesTable
        companies={query.data || []}
        renderActions={(company) => (
          <div className="flex gap-2">
            <ConfirmDialog
              trigger={<Button size="sm" variant="outline">Activate</Button>}
              title="Activate company"
              description="Restore this company to active status."
              onConfirm={() => mutation.mutate({ id: company.id, action: "activate" })}
            />
            <ConfirmDialog
              trigger={<Button size="sm" variant="outline">Suspend</Button>}
              title="Suspend company"
              description="Suspend this company account."
              onConfirm={() => mutation.mutate({ id: company.id, action: "suspend" })}
            />
            <ConfirmDialog
              trigger={<Button size="sm" variant="destructive">Block</Button>}
              title="Block company"
              description="Block this company account."
              variant="destructive"
              onConfirm={() => mutation.mutate({ id: company.id, action: "block" })}
            />
            <ConfirmDialog
              trigger={<Button size="sm" variant="destructive">Delete</Button>}
              title="Delete company"
              description="Are you sure you want to delete this company? This will also delete all of its employees immediately. This action cannot be undone."
              variant="destructive"
              onConfirm={() => deleteMutation.mutate(company.id)}
            />
          </div>
        )}
      />
    </div>
  );
}
