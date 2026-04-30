"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  createBotIntegration,
  disableBotIntegration,
  enableBotIntegration,
  listBotIntegrations,
} from "@/lib/api/botIntegrations";
import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";

import { BotCard } from "@/components/bots/BotCard";
import { BotFormDrawer, type BotFormValues } from "@/components/bots/BotFormDrawer";
import { BotTable } from "@/components/bots/BotTable";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { Button } from "@/components/ui/button";

export default function TelegramBotsPage() {
  const queryClient = useQueryClient();
  const botsQuery = useQuery({
    queryKey: ["botIntegrations"],
    queryFn: listBotIntegrations,
  });
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    select: normalizeProjectListResponse,
  });

  const createMutation = useMutation({
    mutationFn: (values: BotFormValues) =>
      createBotIntegration({
        project_id: values.project_id,
        name: values.name,
        bot_token: values.bot_token || "",
        fallback_message: values.fallback_message,
        human_handoff_enabled: values.human_handoff_enabled,
        show_sources_to_customer: values.show_sources_to_customer,
      }),
    onSuccess: () => {
      toast.success("Bot integration created");
      queryClient.invalidateQueries({ queryKey: ["botIntegrations"] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      enabled ? disableBotIntegration(id) : enableBotIntegration(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["botIntegrations"] }),
  });

  if (botsQuery.isLoading || projectsQuery.isLoading) {
    return <LoadingState label="Loading Telegram bots..." />;
  }

  if (botsQuery.isError || projectsQuery.isError) {
    return <ErrorState description="Failed to load Telegram bots." />;
  }

  const bots = botsQuery.data || [];
  const projects = projectsQuery.data || [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Integrations"
        title="Telegram Bots"
        description="Saved tokens are never displayed after create or rotation."
        actions={<BotFormDrawer projects={projects} isPending={createMutation.isPending} onSubmit={(values) => createMutation.mutate(values)} />}
      />

      {bots.length === 0 ? (
        <EmptyState title="No Telegram bots" description="Create the first integration when you are ready." />
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-3">
            {bots.map((bot) => (
              <div key={bot.id} className="space-y-3">
                <BotCard bot={bot} />
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => toggleMutation.mutate({ id: bot.id, enabled: bot.status === "active" })}
                >
                  {bot.status === "active" ? "Disable" : "Enable"}
                </Button>
              </div>
            ))}
          </div>
          <BotTable bots={bots} />
        </>
      )}
    </div>
  );
}
