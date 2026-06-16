"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import {
  getAdminCompany,
  listAdminCompanyBotIntegrations,
  listAdminCompanyConversations,
  listAdminCompanyProjects,
} from "@/lib/api/admin";
import { queryKeys } from "@/lib/api/queryKeys";
import { Building2, Bot, FolderKanban, MessagesSquare } from "lucide-react";

import { AdminBotsTable } from "@/components/admin/AdminBotsTable";
import { CompanyDetailTabs } from "@/components/admin/CompanyDetailTabs";
import { PageHeader } from "@/components/layout/PageHeader";
import { AdminConversationsTable } from "@/components/admin/AdminConversationsTable";
import { DataTable } from "@/components/shared/DataTable";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { MetricCard } from "@/components/shared/MetricCard";
import { StatusBadge } from "@/components/shared/StatusBadge";

export default function AdminCompanyDetailPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const companyQuery = useQuery({ queryKey: queryKeys.admin.company(companyId), queryFn: () => getAdminCompany(companyId) });
  const projectsQuery = useQuery({
    queryKey: queryKeys.admin.companyProjects(companyId),
    queryFn: () => listAdminCompanyProjects(companyId),
  });
  const botsQuery = useQuery({
    queryKey: queryKeys.admin.companyBots(companyId),
    queryFn: () => listAdminCompanyBotIntegrations(companyId),
  });
  const conversationsQuery = useQuery({
    queryKey: queryKeys.admin.companyConversations(companyId),
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
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Status" value={<StatusBadge status={company.status} />} icon={<Building2 className="size-4" />} tone="info" />
        <MetricCard title="Projects" value={company.project_count || 0} icon={<FolderKanban className="size-4" />} tone="default" />
        <MetricCard title="Bots" value={company.bot_count || 0} icon={<Bot className="size-4" />} tone="success" />
        <MetricCard title="Conversations" value={company.conversation_count || 0} icon={<MessagesSquare className="size-4" />} tone="warning" />
      </div>
      <CompanyDetailTabs
        overview={
          <div className="grid gap-3 text-sm md:grid-cols-2">
            {[
              ["Username", company.username],
              ["Role", company.role],
              ["Company", company.company_name || "—"],
              ["Created", company.created_at || "—"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg border bg-card p-3 shadow-sm">
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="mt-1 font-medium text-foreground">{value}</p>
              </div>
            ))}
          </div>
        }
        projects={
          <DataTable
            caption="Company projects"
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
