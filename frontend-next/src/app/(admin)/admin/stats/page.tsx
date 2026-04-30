"use client";

import { useQuery } from "@tanstack/react-query";

import { getAdminOverview, getAdminStats } from "@/lib/api/admin";

import { AdminMetricCards } from "@/components/admin/AdminMetricCards";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function AdminStatsPage() {
  const statsQuery = useQuery({ queryKey: ["adminStats"], queryFn: getAdminStats });
  const overviewQuery = useQuery({ queryKey: ["adminOverview"], queryFn: getAdminOverview });

  if (statsQuery.isLoading || overviewQuery.isLoading) {
    return <LoadingState label="Loading admin stats..." />;
  }

  if (statsQuery.isError || overviewQuery.isError) {
    return <ErrorState description="Failed to load admin stats." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Stats" title="Admin Stats" description="Advanced charts are not exposed by the backend yet, so the page stays metric-first." />
      <AdminMetricCards overview={statsQuery.data || {}} />
      <EmptyState title="Advanced analytics not available yet" description="The backend currently exposes summary metrics rather than time-series chart data." />
    </div>
  );
}
