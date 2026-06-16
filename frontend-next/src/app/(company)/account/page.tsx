"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Building2, Globe2, ShieldCheck, UserRound } from "lucide-react";

import { changePassword, getMe } from "@/lib/api/auth";
import { queryKeys } from "@/lib/api/queryKeys";

import { PageHeader } from "@/components/layout/PageHeader";
import { FormSection } from "@/components/shared/FormSection";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
import { MetricCard } from "@/components/shared/MetricCard";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const schema = z
  .object({
    current_password: z.string().min(1),
    new_password: z.string().min(8),
    confirm_new_password: z.string().min(8),
  })
  .refine((value) => value.new_password === value.confirm_new_password, {
    path: ["confirm_new_password"],
    message: "Passwords do not match",
  });

type FormValues = z.infer<typeof schema>;

export default function AccountPage() {
  const meQuery = useQuery({
    queryKey: queryKeys.me,
    queryFn: getMe,
  });
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_new_password: "",
    },
  });

  const mutation = useMutation({
    mutationFn: changePassword,
    onSuccess: () => {
      toast.success("Password updated");
      form.reset();
    },
  });

  if (meQuery.isLoading) {
    return <LoadingState label="Loading account..." />;
  }

  if (meQuery.isError || !meQuery.data) {
    return <ErrorState description="Failed to load account details." />;
  }

  const user = meQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Account" title={user.username} description="Profile fields remain read-only unless the backend exposes update endpoints." />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Username" value={user.username} icon={<UserRound className="size-4" />} tone="info" />
        <MetricCard title="Role" value={user.role} icon={<ShieldCheck className="size-4" />} tone="default" />
        <MetricCard title="Company" value={user.company_name || "Unset"} icon={<Building2 className="size-4" />} tone="success" />
        <MetricCard title="Website" value={user.company_website || "Unset"} icon={<Globe2 className="size-4" />} tone="warning" />
      </div>
      <FormSection title="Account details">
        <div className="grid gap-3 text-sm md:grid-cols-2">
          <div className="rounded-lg border bg-background p-3">
            <p className="text-xs text-muted-foreground">Status</p>
            <div className="mt-2"><StatusBadge status={user.status} /></div>
          </div>
          <div className="rounded-lg border bg-background p-3">
            <p className="text-xs text-muted-foreground">User ID</p>
            <p className="mt-1 font-medium text-foreground">#{user.id}</p>
          </div>
        </div>
      </FormSection>
      <FormSection title="Change password">
        <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
          <div className="space-y-2">
            <Input type="password" placeholder="Current password" {...form.register("current_password")} />
            <p className="text-xs text-destructive">{form.formState.errors.current_password?.message}</p>
          </div>
          <div className="space-y-2">
            <Input type="password" placeholder="New password" {...form.register("new_password")} />
            <p className="text-xs text-destructive">{form.formState.errors.new_password?.message}</p>
          </div>
          <div className="space-y-2 md:col-span-2">
            <Input type="password" placeholder="Confirm new password" {...form.register("confirm_new_password")} />
            <p className="text-xs text-destructive">{form.formState.errors.confirm_new_password?.message}</p>
          </div>
          <Button type="submit" className="md:col-span-2" disabled={mutation.isPending}>Update password</Button>
        </form>
      </FormSection>
    </div>
  );
}
