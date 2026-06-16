"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Loader2, LockKeyhole, ShieldCheck } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { getHealth } from "@/lib/api/health";
import { login } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { handleAuthenticatedRedirect, refreshCurrentUser } from "@/lib/auth/session";
import { useAuthStore } from "@/store/auth-store";

import { BackendUnavailableBanner } from "@/components/shared/BackendUnavailableBanner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/shared/StatusBadge";

const schema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const accessToken = useAuthStore((state) => state.accessToken);
  const setAccessToken = useAuthStore((state) => state.setAccessToken);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { username: "", password: "" },
  });

  useEffect(() => {
    if (isHydrated && accessToken) {
      handleAuthenticatedRedirect().catch(() => undefined);
    }
  }, [accessToken, isHydrated]);

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
      toast.success(`Welcome back, ${user.username}`);
      handleAuthenticatedRedirect();
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Login failed");
    },
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 px-4 py-10">
      <Card className="w-full max-w-md border-border/80 shadow-xl">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
            <ShieldCheck className="size-5" />
          </div>
          <div>
            <CardTitle className="text-2xl">Sign in to RAGMind</CardTitle>
            <p className="mt-2 text-sm text-muted-foreground">Manage knowledge bases, bots, conversations, and platform operations.</p>
          </div>
          {!healthQuery.isError && healthQuery.data ? (
            <div className="flex justify-center">
              <StatusBadge status={healthQuery.data.status} />
            </div>
          ) : null}
        </CardHeader>
        <CardContent className="space-y-6">

        {healthQuery.isError ? <BackendUnavailableBanner /> : null}

        <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
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
          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? <Loader2 className="size-4 animate-spin" /> : <LockKeyhole className="size-4" />}
            Login
          </Button>
        </form>

        <div className="text-center text-sm text-muted-foreground">
          No account?{" "}
          <Link href="/signup" className="font-medium text-primary">
            Create one
          </Link>
        </div>
        </CardContent>
      </Card>
    </div>
  );
}
