"use client";

import { useQuery } from "@tanstack/react-query";

import { getAdminOverview, listAdminBotIntegrations, listAdminConversations, listAdminCompanies } from "@/lib/api/admin";

import { AdminMetricCards } from "@/components/admin/AdminMetricCards";
import { PageHeader } from "@/components/layout/PageHeader";
import { AdminErrorsFeed } from "@/components/admin/AdminErrorsFeed";
import { CompaniesTable } from "@/components/admin/CompaniesTable";
import { ConversationList } from "@/components/conversations/ConversationList";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function AdminOverviewPage() {
  const overviewQuery = useQuery({ queryKey: ["adminOverview"], queryFn: getAdminOverview });
  const companiesQuery = useQuery({ queryKey: ["adminCompanies"], queryFn: listAdminCompanies });
  const botsQuery = useQuery({ queryKey: ["adminBots"], queryFn: listAdminBotIntegrations });
  const conversationsQuery = useQuery({ queryKey: ["adminConversations"], queryFn: () => listAdminConversations() });

  if (overviewQuery.isLoading || companiesQuery.isLoading || botsQuery.isLoading || conversationsQuery.isLoading) {
    return <LoadingState label="Loading admin overview..." />;
  }

  if (overviewQuery.isError || companiesQuery.isError || botsQuery.isError || conversationsQuery.isError) {
    return <ErrorState description="Failed to load admin overview." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Platform console" title="Admin Overview" description="Platform-owner-only visibility across companies." />
      <AdminMetricCards overview={overviewQuery.data || {}} />
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <CompaniesTable companies={companiesQuery.data || []} />
        <AdminErrorsFeed bots={botsQuery.data || []} />
      </div>
      {(conversationsQuery.data || []).length > 0 ? (
        <ConversationList
          conversations={(conversationsQuery.data || []).map((conversation) => ({
            id: conversation.id,
            owner_id: conversation.owner_id,
            bot_integration_id: conversation.bot_integration_id,
            telegram_customer_id: 0,
            customer_label: `Conversation #${conversation.id}`,
            project_id: conversation.project_id,
            status: conversation.status,
            needs_human: conversation.needs_human,
            last_message_at: conversation.last_message_at,
            last_error: conversation.last_error,
            created_at: conversation.created_at,
            updated_at: conversation.created_at,
            bot_name: undefined,
            assigned_to_user_id: null,
          }))}
        />
      ) : (
        <EmptyState title="No conversations" description="No cross-company conversations have been recorded yet." />
      )}
    </div>
  );
}
