"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { signup } from "@/lib/api/auth";
import { listAdminCompanies } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";
import { isCompanyAdmin, isPlatformOwner } from "@/lib/auth/permissions";
import { useAuthStore } from "@/store/auth-store";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const schema = z
  .object({
    username: z.string().min(3, "Minimum 3 characters"),
    password: z.string().min(8, "Minimum 8 characters"),
    confirmPassword: z.string().min(8, "Confirm your password"),
    role: z.enum(["platform_owner", "company_admin", "employee"]),
    parentId: z.string().optional(),
  })
  .refine((value) => value.password === value.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type FormValues = z.infer<typeof schema>;

export default function SignupPage() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const currentUser = useAuthStore((state) => state.currentUser);
  const isHydrated = useAuthStore((state) => state.isHydrated);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { username: "", password: "", confirmPassword: "", role: "company_admin", parentId: "" },
  });

  // Set default role to employee for company admin creators
  useEffect(() => {
    if (currentUser && isCompanyAdmin(currentUser)) {
      form.setValue("role", "employee");
    }
  }, [currentUser, form]);

  // Protect page: Only Platform Owners and Company Admins can see it
  useEffect(() => {
    if (isHydrated) {
      const allowed = isPlatformOwner(currentUser) || isCompanyAdmin(currentUser);
      if (!accessToken || !currentUser || !allowed) {
        window.location.replace("/login");
      }
    }
  }, [accessToken, currentUser, isHydrated]);

  // Query to fetch all registered companies
  const companiesQuery = useQuery({
    queryKey: ["adminCompanies"],
    queryFn: listAdminCompanies,
    enabled: isHydrated && !!accessToken && !!currentUser && isPlatformOwner(currentUser),
  });

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const targetRole = isCompanyAdmin(currentUser) ? "employee" : values.role;
      const targetParentId = targetRole === "employee"
        ? (isCompanyAdmin(currentUser) ? (currentUser?.id ?? 0) : (values.parentId ? parseInt(values.parentId) : undefined))
        : undefined;
      return signup({ 
        username: values.username, 
        password: values.password,
        role: targetRole,
        parent_id: targetParentId,
      });
    },
    onSuccess: () => {
      toast.success("Account created successfully!");
      if (currentUser && isPlatformOwner(currentUser)) {
        window.location.replace("/admin/companies");
      } else {
        window.location.replace("/dashboard");
      }
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Signup failed"),
  });

  if (!isHydrated || !accessToken || !currentUser || (!isPlatformOwner(currentUser) && !isCompanyAdmin(currentUser))) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader2 className="size-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md space-y-6 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Create account</h1>
          <p className="text-sm text-slate-600">Register a new employee account (Admin Only).</p>
        </div>

        <form
          className="space-y-4"
          onSubmit={form.handleSubmit((values) => {
            if (values.role === "employee" && isPlatformOwner(currentUser) && !values.parentId) {
              form.setError("parentId", { message: "Please select a parent company for the employee" });
              return;
            }
            mutation.mutate(values);
          })}
        >
          <div className="space-y-2">
            <label className="text-sm font-medium">Username</label>
            <Input {...form.register("username")} />
            <p className="text-sm text-rose-600">{form.formState.errors.username?.message}</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Password</label>
            <Input type="password" {...form.register("password")} />
            <p className="text-sm text-rose-600">{form.formState.errors.password?.message}</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Confirm password</label>
            <Input type="password" {...form.register("confirmPassword")} />
            <p className="text-sm text-rose-600">{form.formState.errors.confirmPassword?.message}</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Account Type</label>
            <select
              {...form.register("role")}
              disabled={isCompanyAdmin(currentUser)}
              className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isPlatformOwner(currentUser) && (
                <option value="platform_owner">Platform Owner</option>
              )}
              {isPlatformOwner(currentUser) && (
                <option value="company_admin">Company Admin</option>
              )}
              <option value="employee">Employee</option>
            </select>
            <p className="text-sm text-rose-600">{form.formState.errors.role?.message}</p>
          </div>

          {/* Conditional Dropdown for selecting parent company */}
          {form.watch("role") === "employee" && isPlatformOwner(currentUser) && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Belongs to Company</label>
              {companiesQuery.isLoading ? (
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Loader2 className="size-4 animate-spin" /> Loading companies list...
                </div>
              ) : (
                <select
                  {...form.register("parentId")}
                  className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">-- Select Company --</option>
                  {companiesQuery.data
                    ?.filter((c) => c.role === "company_admin")
                    ?.map((company) => (
                      <option key={company.id} value={String(company.id)}>
                        {company.company_name || company.username}
                      </option>
                    ))}
                </select>
              )}
              <p className="text-sm text-rose-600">{form.formState.errors.parentId?.message}</p>
            </div>
          )}

          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
            Create account
          </Button>
        </form>

        <div className="text-center text-sm text-slate-600">
          <Link href="/admin/companies" className="font-medium text-indigo-600 hover:underline">
            ← Back to Companies
          </Link>
        </div>
      </div>
    </div>
  );
}
