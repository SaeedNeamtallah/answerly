"use client";

import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Bot, MessageSquareText, ShieldCheck, TriangleAlert } from "lucide-react";

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
import { MetricCard } from "@/components/shared/MetricCard";
import { StatusBadge } from "@/components/shared/StatusBadge";

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
        system_prompt: values.system_prompt,
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
  const conversations = conversationsQuery.data || [];
  const escalated = conversations.filter((conversation) => conversation.needs_human || conversation.status === "escalated").length;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Telegram bot"
        title={bot.name}
        description={bot.telegram_username ? (
          <a href={`https://t.me/${bot.telegram_username}`} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline inline-flex items-center gap-1">
            @{bot.telegram_username}
          </a>
        ) : "Telegram username pending"}
        actions={<RotateTokenDialog onSubmit={(token) => rotateMutation.mutate(token)} isPending={rotateMutation.isPending} />}
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Status" value={<StatusBadge status={bot.status} />} icon={<Bot className="size-4" />} tone="info" />
        <MetricCard title="Readiness" value={readinessQuery.data?.ready ? "Ready" : "Review"} icon={<ShieldCheck className="size-4" />} tone={readinessQuery.data?.ready ? "success" : "warning"} />
        <MetricCard title="Conversations" value={conversations.length} icon={<MessageSquareText className="size-4" />} tone="default" />
        <MetricCard title="Needs Human" value={escalated} icon={<TriangleAlert className="size-4" />} tone={escalated > 0 ? "warning" : "success"} />
      </div>
      <BotReadinessChecklist readiness={readinessQuery.data} />
      <div>
        <BotFormDrawer
          projects={projectsQuery.data || []}
          initialValues={bot}
          isPending={updateMutation.isPending}
          triggerLabel="Edit bot"
          onSubmit={(values) => updateMutation.mutate(values)}
        />
      </div>
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
