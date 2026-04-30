"use client";

import { useQuery } from "@tanstack/react-query";

import { listAdminBotIntegrations } from "@/lib/api/admin";

import { AdminErrorsFeed } from "@/components/admin/AdminErrorsFeed";
import { PageHeader } from "@/components/layout/PageHeader";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function AdminErrorsPage() {
  const query = useQuery({ queryKey: ["adminBots"], queryFn: listAdminBotIntegrations });

  if (query.isLoading) {
    return <LoadingState label="Loading admin errors..." />;
  }

  if (query.isError) {
    return <ErrorState description="Failed to load admin error fallback data." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Fallback aggregation"
        title="Admin Errors"
        description="There is no unified `/admin/errors` endpoint, so this page stays honest and surfaces bot last_error values only."
      />
      <AdminErrorsFeed bots={query.data || []} />
    </div>
  );
}
