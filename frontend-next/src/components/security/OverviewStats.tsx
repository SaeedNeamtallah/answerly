"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, ShieldAlert, Zap, AlertTriangle, UserX } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { securityApi } from "@/lib/api/security";
import { Skeleton } from "@/components/ui/skeleton";

export function OverviewStats() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["security-stats"],
    queryFn: securityApi.getStats,
    refetchInterval: 30000, // Refresh every 30s
  });

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        Failed to load security statistics.
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card className="shadow-sm relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">
            Total Events
          </CardTitle>
          <Activity className="size-4 text-indigo-600" />
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-slate-900">
            {isLoading ? <Skeleton className="h-9 w-20" /> : stats?.total_events.toLocaleString()}
          </div>
          <p className="text-xs text-slate-500 mt-1">Logged across platform</p>
        </CardContent>
      </Card>

      <Card className="shadow-sm relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">
            Login Failures
          </CardTitle>
          <AlertTriangle className="size-4 text-amber-600" />
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-slate-900">
            {isLoading ? <Skeleton className="h-9 w-20" /> : stats?.login_failures.toLocaleString()}
          </div>
          <p className="text-xs text-slate-500 mt-1">Failed authentications</p>
        </CardContent>
      </Card>

      <Card className="shadow-sm relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">
            Brute Force
          </CardTitle>
          <ShieldAlert className="size-4 text-red-600" />
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-slate-900">
            {isLoading ? <Skeleton className="h-9 w-20" /> : stats?.brute_force_attempts.toLocaleString()}
          </div>
          <p className="text-xs text-slate-500 mt-1">Detected attacks</p>
        </CardContent>
      </Card>

      <Card className="shadow-sm relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">
            Blocked Uploads
          </CardTitle>
          <UserX className="size-4 text-cyan-600" />
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-slate-900">
            {isLoading ? <Skeleton className="h-9 w-20" /> : stats?.blocked_uploads.toLocaleString()}
          </div>
          <p className="text-xs text-slate-500 mt-1">Malicious file blocks</p>
        </CardContent>
      </Card>
    </div>
  );
}
