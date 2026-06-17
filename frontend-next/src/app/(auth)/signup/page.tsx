"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Loader2, LockKeyhole, UserPlus, UserRound } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { signup, googleLogin } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { GoogleLogin } from "@react-oauth/google";
import { handleAuthenticatedRedirect, refreshCurrentUser } from "@/lib/auth/session";
import { useAuthStore } from "@/store/auth-store";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  const setAccessToken = useAuthStore((state) => state.setAccessToken);
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
    <div className="w-full max-w-md">
      <Card className="border-0 shadow-xl lg:border-border/50 lg:shadow-2xl">
        <CardHeader className="space-y-4 px-8 pb-0 pt-8">
          <div className="flex w-full border-b">
            <Link
              href="/login"
              className="flex-1 border-b-2 border-transparent pb-3 text-center text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              Login
            </Link>
            <Link
              href="/signup"
              className="flex-1 border-b-2 border-primary pb-3 text-center text-sm font-semibold text-primary"
            >
              Sign Up
            </Link>
          </div>
          
          <div className="pt-6 text-center">
            <CardTitle className="text-2xl text-[#162758]">Create your account</CardTitle>
            <p className="mt-1 text-sm font-medium text-blue-600">Step 1 of 2</p>
          </div>
        </CardHeader>
        <CardContent className="space-y-6 px-8 pb-8 pt-6">

        <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">Username</label>
            <div className="relative">
              <UserRound className="absolute left-3 top-3 size-4 text-muted-foreground" />
              <Input className="pl-9 h-11" placeholder="jane.doe" {...form.register("username")} />
            </div>
            <p className="text-xs text-rose-600">{form.formState.errors.username?.message}</p>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">Password</label>
            <div className="relative">
              <LockKeyhole className="absolute left-3 top-3 size-4 text-muted-foreground" />
              <Input type="password" placeholder="••••••••••••" className="pl-9 h-11" {...form.register("password")} />
            </div>
            <p className="text-xs text-rose-600">{form.formState.errors.password?.message}</p>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">Confirm password</label>
            <div className="relative">
              <LockKeyhole className="absolute left-3 top-3 size-4 text-muted-foreground" />
              <Input type="password" placeholder="••••••••••••" className="pl-9 h-11" {...form.register("confirmPassword")} />
            </div>
            <p className="text-xs text-rose-600">{form.formState.errors.confirmPassword?.message}</p>
          </div>

          <div className="flex items-center space-x-2 pt-2">
            <input 
              type="checkbox" 
              id="terms" 
              className="size-4 rounded border-gray-300 text-blue-600 focus:ring-blue-600"
              required 
            />
            <label
              htmlFor="terms"
              className="text-xs text-slate-600"
            >
              I agree to the <a href="#" className="text-blue-600 hover:underline">Terms of Service</a> and <a href="#" className="text-blue-600 hover:underline">Privacy Policy</a>
            </label>
          </div>

          <Button type="submit" className="h-11 w-full rounded-lg bg-blue-600 hover:bg-blue-700" disabled={mutation.isPending}>
            {mutation.isPending ? <Loader2 className="mr-2 size-4 animate-spin" /> : null}
            Create account
          </Button>

          <div className="relative py-2">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-white px-4 text-muted-foreground">Or sign up with</span>
            </div>
          </div>
          
          <div className="flex justify-center">
            {process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ? (
              <GoogleLogin
                onSuccess={async (credentialResponse) => {
                  if (credentialResponse.credential) {
                    try {
                      const payload = await googleLogin(credentialResponse.credential);
                      setAccessToken(payload.access_token);
                      const user = await refreshCurrentUser();
                      toast.success(`Welcome back, ${user.username}`);
                      handleAuthenticatedRedirect();
                    } catch (error) {
                      toast.error(error instanceof ApiError ? error.message : "Google login failed");
                    }
                  }
                }}
                onError={() => {
                  toast.error("Google Login Failed");
                }}
              />
            ) : (
              <Button type="button" variant="outline" className="w-full h-11" onClick={() => toast.error("Google Login is not configured (missing Client ID).")}>
                <svg className="mr-2 h-4 w-4" aria-hidden="true" focusable="false" data-prefix="fab" data-icon="google" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 488 512">
                  <path fill="currentColor" d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 24.9 3.9 41.4z"></path>
                </svg>
                Sign in with Google
              </Button>
            )}
          </div>
          
        </form>

        <div className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-blue-600 hover:underline">
            Login
          </Link>
        </div>
        </CardContent>
      </Card>
    </div>
  );
}
