"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { signup } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const schema = z
  .object({
    username: z.string().min(3, "Minimum 3 characters"),
    password: z.string().min(8, "Minimum 8 characters"),
    confirmPassword: z.string().min(8, "Confirm your password"),
  })
  .refine((value) => value.password === value.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type FormValues = z.infer<typeof schema>;

export default function SignupPage() {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { username: "", password: "", confirmPassword: "" },
  });

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => signup({ username: values.username, password: values.password }),
    onSuccess: () => {
      toast.success("Account created. You can now sign in.");
      window.location.replace("/login");
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Signup failed"),
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md space-y-6 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Create account</h1>
          <p className="text-sm text-slate-600">This preserves the existing `/auth/signup` backend flow.</p>
        </div>

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
          <div className="space-y-2">
            <label className="text-sm font-medium">Confirm password</label>
            <Input type="password" {...form.register("confirmPassword")} />
            <p className="text-sm text-rose-600">{form.formState.errors.confirmPassword?.message}</p>
          </div>
          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
            Create account
          </Button>
        </form>

        <div className="text-center text-sm text-slate-600">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-indigo-600">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
