"use client";

import { useQuery } from "@tanstack/react-query";
import { Bot, MessageSquareText, UserRound, Send, BookOpen, FileWarning } from "lucide-react";

import { listBotIntegrations } from "@/lib/api/botIntegrations";
import { ApiError } from "@/lib/api/client";
import { listConversations } from "@/lib/api/conversations";
import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";
import { queryKeys } from "@/lib/api/queryKeys";
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
    queryKey: queryKeys.projects.all,
    queryFn: listProjects,
    select: normalizeProjectListResponse,
  });
  const botsQuery = useQuery({
    queryKey: queryKeys.bots.all,
    queryFn: listBotIntegrations,
  });
  const conversationsQuery = useQuery({
    queryKey: queryKeys.conversations.filtered("recent"),
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
  const openConversations = conversations.filter((conversation) => conversation.status === "open").length;
  const needsHuman = conversations.filter((conversation) => conversation.needs_human).length;
  const activeBots = bots.filter((bot) => ["active", "online", "ready"].includes(String(bot.status).toLowerCase())).length;
  const botIssues = bots.filter((bot) => bot.last_error).length;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Dashboard"
        description="Overview of your bots, conversations, and knowledge assets."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        <MetricCard
          title="Active Bots"
          value={formatNumber(activeBots)}
          tone="success"
          icon={<Bot fill="currentColor" />}
        />
        <MetricCard
          title="Bot Issues"
          value={formatNumber(botIssues)}
          tone="danger"
          icon={<FileWarning fill="currentColor" />}
        />
        <MetricCard
          title="Open Chats"
          value={formatNumber(openConversations)}
          tone="info"
          icon={<MessageSquareText fill="currentColor" />}
        />
        <MetricCard
          title="Needs Human"
          value={formatNumber(needsHuman)}
          tone="warning"
          icon={<UserRound fill="currentColor" />}
        />
        <MetricCard
          title="Total Chats"
          value={formatNumber(conversations.length)}
          tone="default"
          icon={<Send fill="currentColor" className="ml-1" />}
        />
        <MetricCard
          title="Knowledge Bases"
          value={formatNumber(projects.length)}
          tone="purple"
          icon={<BookOpen fill="currentColor" />}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
        <SetupChecklist projects={projects} bots={bots} conversations={conversations} />
        <BotHealthPanel bots={bots} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <RecentConversations conversations={conversations} />
        <KnowledgeBaseReadiness projects={projects} bots={bots} />
      </div>
    </div>
  );
}
