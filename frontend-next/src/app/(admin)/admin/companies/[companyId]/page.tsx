"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import {
  getAdminCompany,
  listAdminCompanyBotIntegrations,
  listAdminCompanyConversations,
  listAdminCompanyProjects,
} from "@/lib/api/admin";

import { AdminBotsTable } from "@/components/admin/AdminBotsTable";
import { CompanyDetailTabs } from "@/components/admin/CompanyDetailTabs";
import { PageHeader } from "@/components/layout/PageHeader";
import { AdminConversationsTable } from "@/components/admin/AdminConversationsTable";
import { DataTable } from "@/components/shared/DataTable";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function AdminCompanyDetailPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const companyQuery = useQuery({ queryKey: ["adminCompany", companyId], queryFn: () => getAdminCompany(companyId) });
  const projectsQuery = useQuery({
    queryKey: ["adminCompanyProjects", companyId],
    queryFn: () => listAdminCompanyProjects(companyId),
  });
  const botsQuery = useQuery({
    queryKey: ["adminCompanyBots", companyId],
    queryFn: () => listAdminCompanyBotIntegrations(companyId),
  });
  const conversationsQuery = useQuery({
    queryKey: ["adminCompanyConversations", companyId],
    queryFn: () => listAdminCompanyConversations(companyId),
  });

  if (companyQuery.isLoading || projectsQuery.isLoading || botsQuery.isLoading || conversationsQuery.isLoading) {
    return <LoadingState label="Loading company detail..." />;
  }

  if (companyQuery.isError || projectsQuery.isError || botsQuery.isError || conversationsQuery.isError) {
    return <ErrorState description="Failed to load company detail." />;
  }

  const company = companyQuery.data!;

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Company detail" title={company.company_name || company.username} description="Read-only aggregate visibility for platform owners." />
      <CompanyDetailTabs
        overview={
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm text-sm text-slate-600 space-y-2">
            <p>Role: {company.role}</p>
            <p>Status: {company.status}</p>
            <p>Projects: {company.project_count}</p>
            <p>Bots: {company.bot_count}</p>
            <p>Conversations: {company.conversation_count}</p>
          </div>
        }
        projects={
          <DataTable
            columns={["Project", "Description"]}
            rows={(projectsQuery.data || []).map((project) => [project.name, project.description || "—"])}
          />
        }
        bots={<AdminBotsTable bots={botsQuery.data || []} />}
        conversations={<AdminConversationsTable conversations={conversationsQuery.data || []} />}
      />
    </div>
  );
}
