"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Loader2, ShieldCheck } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { getHealth } from "@/lib/api/health";
import { login } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { handleAuthenticatedRedirect, refreshCurrentUser, isTokenExpired } from "@/lib/auth/session";
import { isPlatformOwner } from "@/lib/auth/permissions";
import { useAuthStore } from "@/store/auth-store";

import { BackendUnavailableBanner } from "@/components/shared/BackendUnavailableBanner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const schema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
  role: z.enum(["admin", "company", "employee"]),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const accessToken = useAuthStore((state) => state.accessToken);
  const currentUser = useAuthStore((state) => state.currentUser);
  const setAccessToken = useAuthStore((state) => state.setAccessToken);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { username: "", password: "", role: "company" },
  });

  useEffect(() => {
    if (isHydrated && accessToken && currentUser && !isTokenExpired(accessToken)) {
      handleAuthenticatedRedirect().catch(() => undefined);
    }
  }, [accessToken, currentUser, isHydrated]);

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: 0,
  });

  const mutation = useMutation({
    mutationFn: login,
    onSuccess: async (payload) => {
      setAccessToken(payload.access_token);
      const user = await refreshCurrentUser();
      
      // Get the selected user type from form values
      const selectedRole = form.getValues("role");
      
      // Enforce security checks based on selected login role and actual DB role
      if (selectedRole === "admin" && user.role !== "platform_owner") {
        toast.error("Access Denied: You do not have Platform Owner (Admin) permissions.");
        useAuthStore.getState().clearSession();
        return;
      }
      if (selectedRole === "company" && user.role !== "company_admin" && user.role !== "platform_owner") {
        toast.error("Access Denied: This account is not registered as a Company Admin.");
        useAuthStore.getState().clearSession();
        return;
      }
      if (selectedRole === "employee" && user.role !== "employee" && user.role !== "platform_owner") {
        toast.error("Access Denied: This account is not registered as an Employee.");
        useAuthStore.getState().clearSession();
        return;
      }
      
      toast.success(`Welcome back, ${user.username}`);

      // Direct according to selected type
      if (selectedRole === "admin") {
        window.location.replace("/admin");
      } else if (selectedRole === "employee") {
        window.location.replace("/conversations");
      } else {
        window.location.replace("/dashboard");
      }
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Login failed");
    },
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md space-y-6 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="space-y-2 text-center">
          <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-indigo-600 text-white">
            <ShieldCheck className="size-5" />
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Sign in to RAGMind</h1>
          <p className="text-sm text-slate-600">JWT bearer auth remains compatible with the existing backend.</p>
        </div>

        {healthQuery.isError ? <BackendUnavailableBanner /> : null}

        <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate({ username: values.username, password: values.password }))}>
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
            <label className="text-sm font-medium">User Type </label>
            <select
              {...form.register("role")}
              className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="admin">Platform Owner </option>
              <option value="company">Company Admin </option>
              <option value="employee">Employee </option>
            </select>
            <p className="text-sm text-rose-600">{form.formState.errors.role?.message}</p>
          </div>
          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
            Login
          </Button>
        </form>
      </div>
    </div>
  );
}
