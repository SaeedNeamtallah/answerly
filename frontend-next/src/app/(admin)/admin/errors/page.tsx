"use client";

import { useQuery } from "@tanstack/react-query";

import { listAdminBotIntegrations } from "@/lib/api/admin";
import { queryKeys } from "@/lib/api/queryKeys";

import { AdminErrorsFeed } from "@/components/admin/AdminErrorsFeed";
import { PageHeader } from "@/components/layout/PageHeader";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function AdminErrorsPage() {
  const query = useQuery({ queryKey: queryKeys.admin.bots, queryFn: listAdminBotIntegrations });

  if (query.isLoading) {
    return <LoadingState label="Loading admin errors..." />;
  }

  if (query.isError) {
    return <ErrorState description="Failed to load admin error fallback data." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Operational errors"
        title="Admin Errors"
        description="Bot integration errors reported by the platform-owner inventory endpoint."
      />
      <AdminErrorsFeed bots={query.data || []} />
    </div>
  );
}
