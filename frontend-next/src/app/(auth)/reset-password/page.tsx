"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Loader2, KeyRound } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { resetPassword } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const schema = z
  .object({
    password: z.string().min(8, "Minimum 8 characters"),
    confirmPassword: z.string().min(8, "Confirm your password"),
  })
  .refine((value) => value.password === value.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type FormValues = z.infer<typeof schema>;

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const router = useRouter();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { password: "", confirmPassword: "" },
  });

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => resetPassword({ token: token || "", new_password: values.password }),
    onSuccess: () => {
      toast.success("Password reset successfully. You can now sign in.");
      router.push("/login");
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Failed to reset password"),
  });

  if (!token) {
    return (
      <div className="text-center space-y-4">
        <p className="text-rose-600">Invalid or missing reset token.</p>
        <Button variant="outline" onClick={() => router.push("/forgot-password")}>
          Request New Link
        </Button>
      </div>
    );
  }

  return (
    <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <div className="space-y-2">
        <label className="text-sm font-medium">New Password</label>
        <Input type="password" {...form.register("password")} />
        <p className="text-sm text-rose-600">{form.formState.errors.password?.message}</p>
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium">Confirm New Password</label>
        <Input type="password" {...form.register("confirmPassword")} />
        <p className="text-sm text-rose-600">{form.formState.errors.confirmPassword?.message}</p>
      </div>
      <Button type="submit" className="w-full" disabled={mutation.isPending}>
        {mutation.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
        Reset Password
      </Button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 px-4 py-10">
      <Card className="w-full max-w-md border-border/80 shadow-xl">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
            <KeyRound className="size-5" />
          </div>
          <div>
            <CardTitle className="text-2xl">Create New Password</CardTitle>
            <CardDescription className="mt-2">Enter your new password below.</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <Suspense fallback={<div className="flex justify-center"><Loader2 className="size-6 animate-spin" /></div>}>
            <ResetPasswordForm />
          </Suspense>

          <div className="text-center text-sm text-muted-foreground">
            Remember your password?{" "}
            <Link href="/login" className="font-medium text-primary">
              Sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
