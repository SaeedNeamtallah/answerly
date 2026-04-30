"use client";

import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  deleteBotIntegration,
  getBotIntegration,
  getBotReadiness,
  rotateBotToken,
  updateBotIntegration,
} from "@/lib/api/botIntegrations";
import { listConversations } from "@/lib/api/conversations";
import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";

import { BotFormDrawer, type BotFormValues } from "@/components/bots/BotFormDrawer";
import { BotReadinessChecklist } from "@/components/bots/BotReadinessChecklist";
import { RotateTokenDialog } from "@/components/bots/RotateTokenDialog";
import { PageHeader } from "@/components/layout/PageHeader";
import { ConversationList } from "@/components/conversations/ConversationList";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { DangerZone } from "@/components/shared/DangerZone";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { Button } from "@/components/ui/button";

export default function TelegramBotDetailPage() {
  const { botId } = useParams<{ botId: string }>();
  const queryClient = useQueryClient();

  const botQuery = useQuery({
    queryKey: ["botIntegration", botId],
    queryFn: () => getBotIntegration(botId),
  });
  const readinessQuery = useQuery({
    queryKey: ["botReadiness", botId],
    queryFn: () => getBotReadiness(botId),
  });
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    select: normalizeProjectListResponse,
  });
  const conversationsQuery = useQuery({
    queryKey: ["conversations", "bot", botId],
    queryFn: () => listConversations(),
    select: (items) => items.filter((conversation) => String(conversation.bot_integration_id) === botId),
  });

  const updateMutation = useMutation({
    mutationFn: (values: BotFormValues) =>
      updateBotIntegration(botId, {
        name: values.name,
        project_id: values.project_id,
        fallback_message: values.fallback_message,
        show_sources_to_customer: values.show_sources_to_customer,
        human_handoff_enabled: values.human_handoff_enabled,
      }),
    onSuccess: () => {
      toast.success("Bot updated");
      queryClient.invalidateQueries({ queryKey: ["botIntegration", botId] });
      queryClient.invalidateQueries({ queryKey: ["botIntegrations"] });
    },
  });

  const rotateMutation = useMutation({
    mutationFn: (token: string) => rotateBotToken(botId, { bot_token: token }),
    onSuccess: () => {
      toast.success("Bot token rotated");
      queryClient.invalidateQueries({ queryKey: ["botIntegration", botId] });
      queryClient.invalidateQueries({ queryKey: ["botReadiness", botId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteBotIntegration(botId),
    onSuccess: () => {
      toast.success("Bot deleted");
      queryClient.invalidateQueries({ queryKey: ["botIntegrations"] });
      window.location.replace("/telegram-bots");
    },
  });

  if (botQuery.isLoading || readinessQuery.isLoading || projectsQuery.isLoading || conversationsQuery.isLoading) {
    return <LoadingState label="Loading bot details..." />;
  }

  if (botQuery.isError || readinessQuery.isError || projectsQuery.isError || conversationsQuery.isError) {
    return <ErrorState description="Failed to load bot details." />;
  }

  const bot = botQuery.data!;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Telegram bot"
        title={bot.name}
        description={bot.telegram_username || "Telegram username pending"}
        actions={<RotateTokenDialog onSubmit={(token) => rotateMutation.mutate(token)} isPending={rotateMutation.isPending} />}
      />
      <BotReadinessChecklist readiness={readinessQuery.data} />
      <BotFormDrawer
        projects={projectsQuery.data || []}
        initialValues={bot}
        isPending={updateMutation.isPending}
        triggerLabel="Edit bot"
        onSubmit={(values) => updateMutation.mutate(values)}
      />
      <ConversationList conversations={conversationsQuery.data || []} />
      <DangerZone title="Danger zone" description="Deleting this integration also removes it from the dashboard.">
        <ConfirmDialog
          trigger={<Button variant="destructive">Delete bot</Button>}
          title="Delete bot"
          description="This permanently removes the integration. Saved token values are never shown."
          variant="destructive"
          onConfirm={() => deleteMutation.mutate()}
        />
      </DangerZone>
    </div>
  );
}
