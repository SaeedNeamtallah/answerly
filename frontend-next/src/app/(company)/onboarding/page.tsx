"use client";

import { useQuery } from "@tanstack/react-query";

import { listBotIntegrations } from "@/lib/api/botIntegrations";
import { listConversations } from "@/lib/api/conversations";
import { queryKeys } from "@/lib/api/queryKeys";
import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";

import { PageHeader } from "@/components/layout/PageHeader";
import { SetupChecklist } from "@/components/dashboard/SetupChecklist";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function OnboardingPage() {
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
    queryKey: queryKeys.conversations.all,
    queryFn: () => listConversations(),
  });

  if (projectsQuery.isLoading || botsQuery.isLoading || conversationsQuery.isLoading) {
    return <LoadingState label="Loading onboarding..." />;
  }

  if (projectsQuery.isError || botsQuery.isError || conversationsQuery.isError) {
    return <ErrorState description="Failed to load onboarding progress." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Getting started"
        title="Onboarding"
        description="Follow the backend-connected steps needed to run a company workspace."
      />
      <SetupChecklist
        projects={projectsQuery.data || []}
        bots={botsQuery.data || []}
        conversations={conversationsQuery.data || []}
      />
    </div>
  );
}
