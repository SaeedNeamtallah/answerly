"use client";

import { useQuery } from "@tanstack/react-query";

import { listAdminConversations } from "@/lib/api/admin";
import { queryKeys } from "@/lib/api/queryKeys";

import { AdminConversationsTable } from "@/components/admin/AdminConversationsTable";
import { PageHeader } from "@/components/layout/PageHeader";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function AdminConversationsPage() {
  const query = useQuery({ queryKey: queryKeys.admin.conversations, queryFn: () => listAdminConversations() });

  if (query.isLoading) {
    return <LoadingState label="Loading admin conversations..." />;
  }

  if (query.isError) {
    return <ErrorState description="Failed to load admin conversations." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Read-only" title="Admin Conversations" description="Cross-company conversation visibility for platform owners." />
      <AdminConversationsTable conversations={query.data || []} />
    </div>
  );
}
