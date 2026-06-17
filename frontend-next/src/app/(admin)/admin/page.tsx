"use client";

import { useQuery } from "@tanstack/react-query";
import { Settings2, RotateCcw, Building2 } from "lucide-react";

import { getAdminOverview, listAdminBotIntegrations, listAdminConversations, listAdminCompanies } from "@/lib/api/admin";
import { queryKeys } from "@/lib/api/queryKeys";

import { AdminMetricCards } from "@/components/admin/AdminMetricCards";
import { AdminErrorsFeed } from "@/components/admin/AdminErrorsFeed";
import { CompaniesTable } from "@/components/admin/CompaniesTable";
import { ConversationList } from "@/components/conversations/ConversationList";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { Button } from "@/components/ui/button";

export default function AdminOverviewPage() {
  const overviewQuery = useQuery({ queryKey: queryKeys.admin.overview, queryFn: getAdminOverview });
  const companiesQuery = useQuery({ queryKey: queryKeys.admin.companies, queryFn: listAdminCompanies });
  const botsQuery = useQuery({ queryKey: queryKeys.admin.bots, queryFn: listAdminBotIntegrations });
  const conversationsQuery = useQuery({ queryKey: queryKeys.admin.conversations, queryFn: () => listAdminConversations() });

  if (overviewQuery.isLoading || companiesQuery.isLoading || botsQuery.isLoading || conversationsQuery.isLoading) {
    return <LoadingState label="Loading admin overview..." />;
  }

  if (overviewQuery.isError || companiesQuery.isError || botsQuery.isError || conversationsQuery.isError) {
    return <ErrorState description="Failed to load admin overview." />;
  }

  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Admin Overview</h1>
          <p className="text-sm text-slate-500 mt-1">
            Platform-owner-only visibility across companies.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="h-10 rounded-xl px-4 border-slate-200 text-slate-600 bg-white">
            <RotateCcw className="size-4 mr-2" />
            Refresh Data
          </Button>
          <Button className="h-10 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm px-4">
            <Settings2 className="mr-2 size-4" />
            Platform Settings
          </Button>
        </div>
      </div>

      <AdminMetricCards overview={overviewQuery.data || {}} />
      
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <CompaniesTable companies={companiesQuery.data || []} />
        <AdminErrorsFeed bots={botsQuery.data || []} />
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-slate-900 tracking-tight flex items-center gap-2">
          Platform Conversations
        </h2>
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
          <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-sm">
            <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-slate-50 text-slate-400 mb-4">
              <Building2 className="size-6" />
            </div>
            <h3 className="text-sm font-medium text-slate-900">No conversations</h3>
            <p className="mt-1 text-sm text-slate-500">No cross-company conversations have been recorded yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
