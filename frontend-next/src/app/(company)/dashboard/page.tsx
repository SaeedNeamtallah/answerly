"use client";

import { useQuery } from "@tanstack/react-query";
import { Bot, FolderKanban, MessageSquareText } from "lucide-react";

import { listBotIntegrations } from "@/lib/api/botIntegrations";
import { listConversations } from "@/lib/api/conversations";
import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";
import { ApiError } from "@/lib/api/client";
import { formatNumber } from "@/lib/utils/formatters";

import { BotHealthPanel } from "@/components/dashboard/BotHealthPanel";
import { KnowledgeBaseReadiness } from "@/components/dashboard/KnowledgeBaseReadiness";
import { RecentConversations } from "@/components/dashboard/RecentConversations";
import { SetupChecklist } from "@/components/dashboard/SetupChecklist";
import { PageHeader } from "@/components/layout/PageHeader";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { MetricCard } from "@/components/shared/MetricCard";

export default function DashboardPage() {
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    select: normalizeProjectListResponse,
  });
  const botsQuery = useQuery({
    queryKey: ["botIntegrations"],
    queryFn: listBotIntegrations,
  });
  const conversationsQuery = useQuery({
    queryKey: ["conversations", "recent"],
    queryFn: () => listConversations(),
  });

  if (projectsQuery.isLoading || botsQuery.isLoading || conversationsQuery.isLoading) {
    return <LoadingState label="Loading dashboard..." />;
  }

  if (projectsQuery.isError || botsQuery.isError || conversationsQuery.isError) {
    const error =
      (projectsQuery.error as ApiError | undefined) ||
      (botsQuery.error as ApiError | undefined) ||
      (conversationsQuery.error as ApiError | undefined);

    return <ErrorState description={error?.message || "Failed to load dashboard"} />;
  }

  const projects = projectsQuery.data || [];
  const bots = botsQuery.data || [];
  const conversations = conversationsQuery.data || [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Company workspace"
        title="Dashboard"
        description="Projects are presented as knowledge bases while preserving the backend domain model."
      />
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard title="Knowledge Bases" value={formatNumber(projects.length)} icon={<FolderKanban className="size-4 text-indigo-600" />} />
        <MetricCard title="Telegram Bots" value={formatNumber(bots.length)} icon={<Bot className="size-4 text-indigo-600" />} />
        <MetricCard
          title="Conversations"
          value={formatNumber(conversations.length)}
          icon={<MessageSquareText className="size-4 text-indigo-600" />}
        />
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
        <SetupChecklist />
        <KnowledgeBaseReadiness projects={projects} />
      </div>
      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <BotHealthPanel bots={bots} />
        <RecentConversations conversations={conversations} />
      </div>
    </div>
  );
}
