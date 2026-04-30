"use client";

import { useQuery } from "@tanstack/react-query";

import { listAdminBotIntegrations } from "@/lib/api/admin";

import { AdminBotsTable } from "@/components/admin/AdminBotsTable";
import { PageHeader } from "@/components/layout/PageHeader";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function AdminBotsPage() {
  const query = useQuery({ queryKey: ["adminBots"], queryFn: listAdminBotIntegrations });

  if (query.isLoading) {
    return <LoadingState label="Loading admin bots..." />;
  }

  if (query.isError) {
    return <ErrorState description="Failed to load admin bots." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Read-only" title="Admin Bots" description="Cross-company bot inventory for platform owners." />
      <AdminBotsTable bots={query.data || []} />
    </div>
  );
}
