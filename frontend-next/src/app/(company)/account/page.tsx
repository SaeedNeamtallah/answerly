"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { changePassword, getMe } from "@/lib/api/auth";

import { PageHeader } from "@/components/layout/PageHeader";
import { FormSection } from "@/components/shared/FormSection";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";
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
    queryKey: ["me"],
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
      <FormSection title="Account details">
        <div className="grid gap-3 md:grid-cols-2 text-sm text-slate-600">
          <p>Role: {user.role}</p>
          <p>Status: {user.status || "—"}</p>
          <p>Company: {user.company_name || "—"}</p>
          <p>Website: {user.company_website || "—"}</p>
        </div>
      </FormSection>
      <FormSection title="Change password">
        <form className="grid gap-4 md:grid-cols-2" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
          <Input type="password" placeholder="Current password" {...form.register("current_password")} />
          <Input type="password" placeholder="New password" {...form.register("new_password")} />
          <Input type="password" placeholder="Confirm new password" {...form.register("confirm_new_password")} />
          <Button type="submit" className="md:col-span-2">Update password</Button>
        </form>
      </FormSection>
    </div>
  );
}
