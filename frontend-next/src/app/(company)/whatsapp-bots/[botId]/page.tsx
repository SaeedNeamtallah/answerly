"use client";

import Image from "next/image";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { MessageSquareText, ShieldCheck, TriangleAlert, MessageSquare, QrCode } from "lucide-react";

import {
  deleteWhatsAppIntegration,
  getWhatsAppIntegration,
  updateWhatsAppIntegration,
  connectWhatsAppSession,
  getWhatsAppSessionStatus,
} from "@/lib/api/whatsappIntegrations";
import { listConversations } from "@/lib/api/conversations";
import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";

import { WhatsAppBotFormDrawer, type BotFormValues } from "@/components/whatsapp-bots/WhatsAppBotFormDrawer";
import { PageHeader } from "@/components/layout/PageHeader";
import { ConversationList } from "@/components/conversations/ConversationList";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { DangerZone } from "@/components/shared/DangerZone";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/shared/MetricCard";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { getApiErrorMessage } from "@/lib/api/client";
import QRCode from 'qrcode';
import { useEffect, useState } from "react";

function WhatsAppConnectionManager({ botId }: { botId: string }) {
  const queryClient = useQueryClient();
  const [qrImageUrl, setQrImageUrl] = useState<string | null>(null);

  const statusQuery = useQuery({
    queryKey: ["whatsappSessionStatus", botId],
    queryFn: () => getWhatsAppSessionStatus(Number(botId)),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'initializing' || status === 'qr_ready') return 3000;
      return false;
    },
  });

  const connectMutation = useMutation({
    mutationFn: () => connectWhatsAppSession(Number(botId)),
    onSuccess: () => {
      toast.success("Connection process started");
      queryClient.invalidateQueries({ queryKey: ["whatsappSessionStatus", botId] });
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to start WhatsApp connection."));
    },
  });

  useEffect(() => {
    let isActive = true;
    if (statusQuery.data?.qr) {
      QRCode.toDataURL(statusQuery.data.qr).then((url) => {
        if (isActive) {
          setQrImageUrl(url);
        }
      });
    }
    return () => {
      isActive = false;
    };
  }, [statusQuery.data?.qr]);

  const status = statusQuery.data?.status;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-3 mb-4">
        <QrCode className="size-5 text-slate-500" />
        <h3 className="font-semibold text-slate-900">WhatsApp Connection</h3>
      </div>
      
      {status === 'connected' ? (
        <div className="bg-emerald-50 text-emerald-700 p-4 rounded-xl border border-emerald-100 flex items-center gap-3">
          <ShieldCheck className="size-5" />
          <p className="font-medium">WhatsApp is connected and ready to receive messages.</p>
        </div>
      ) : status === 'qr_ready' && qrImageUrl ? (
        <div className="space-y-4">
          <p className="text-sm text-slate-600">Scan this QR code with your WhatsApp app to link your account.</p>
          <div className="flex justify-center p-4 bg-slate-50 rounded-xl border border-slate-100">
            <Image src={qrImageUrl} alt="WhatsApp QR Code" width={256} height={256} unoptimized className="size-64 object-contain" />
          </div>
        </div>
      ) : status === 'initializing' ? (
        <div className="text-sm text-slate-600 flex items-center gap-2">
          <div className="size-4 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
          Initializing session, please wait...
        </div>
      ) : status === 'expired' || status === 'error' ? (
        <div className="space-y-4">
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            {statusQuery.data?.last_error || "The WhatsApp session could not be completed. Start a new connection and scan the fresh QR code."}
          </div>
          <Button onClick={() => connectMutation.mutate()} disabled={connectMutation.isPending}>
            {connectMutation.isPending ? "Starting..." : "Generate New QR Code"}
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            Your WhatsApp integration is not currently connected. Click the button below to generate a QR code for linking your account.
          </p>
          <Button onClick={() => connectMutation.mutate()} disabled={connectMutation.isPending}>
            {connectMutation.isPending ? "Starting..." : "Connect WhatsApp"}
          </Button>
        </div>
      )}
    </div>
  );
}

export default function WhatsAppBotDetailPage() {
  const { botId } = useParams<{ botId: string }>();
  const queryClient = useQueryClient();

  const botQuery = useQuery({
    queryKey: ["whatsappIntegration", botId],
    queryFn: () => getWhatsAppIntegration(Number(botId)),
  });

  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    select: normalizeProjectListResponse,
  });

  const conversationsQuery = useQuery({
    queryKey: ["conversations", "whatsapp", botId],
    queryFn: () => listConversations(),
    select: (items) => items.filter((conversation) => String(conversation.whatsapp_integration_id) === botId),
  });

  const updateMutation = useMutation({
    mutationFn: (values: BotFormValues) =>
      updateWhatsAppIntegration(Number(botId), {
        name: values.name,
        project_id: values.project_id,
        fallback_message: values.fallback_message,
        system_prompt: values.system_prompt,
        show_sources_to_customer: values.show_sources_to_customer,
        human_handoff_enabled: values.human_handoff_enabled,
      }),
    onSuccess: () => {
      toast.success("WhatsApp bot updated");
      queryClient.invalidateQueries({ queryKey: ["whatsappIntegration", botId] });
      queryClient.invalidateQueries({ queryKey: ["whatsappIntegrations"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteWhatsAppIntegration(Number(botId)),
    onSuccess: () => {
      toast.success("WhatsApp bot deleted");
      queryClient.invalidateQueries({ queryKey: ["whatsappIntegrations"] });
      window.location.replace("/whatsapp-bots");
    },
  });

  if (botQuery.isLoading || projectsQuery.isLoading || conversationsQuery.isLoading) {
    return <LoadingState label="Loading WhatsApp bot details..." />;
  }

  if (botQuery.isError || projectsQuery.isError || conversationsQuery.isError) {
    return <ErrorState description="Failed to load WhatsApp bot details." />;
  }

  const bot = botQuery.data!;
  const conversations = conversationsQuery.data || [];
  const escalated = conversations.filter((conversation) => conversation.needs_human || conversation.status === "escalated").length;

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="WhatsApp bot"
        title={bot.name}
        description={bot.phone_number ? bot.phone_number : "No phone number linked"}
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Status" value={<StatusBadge status={bot.status} />} icon={<MessageSquare className="size-4" />} tone="info" />
        <MetricCard title="Conversations" value={conversations.length} icon={<MessageSquareText className="size-4" />} tone="default" />
        <MetricCard title="Needs Human" value={escalated} icon={<TriangleAlert className="size-4" />} tone={escalated > 0 ? "warning" : "success"} />
      </div>
      
      <WhatsAppConnectionManager botId={botId} />
      
      <div>
        <WhatsAppBotFormDrawer
          projects={projectsQuery.data || []}
          initialValues={bot}
          isPending={updateMutation.isPending}
          triggerLabel="Edit WhatsApp Bot"
          onSubmit={(values) => updateMutation.mutate(values)}
        />
      </div>
      <ConversationList conversations={conversationsQuery.data || []} />
      <DangerZone title="Danger zone" description="Deleting this integration also removes it from the dashboard and logs out any active session.">
        <ConfirmDialog
          trigger={<Button variant="destructive">Delete bot</Button>}
          title="Delete WhatsApp Bot"
          description="This permanently removes the integration and session. You will need to re-scan a QR code if you create it again."
          variant="destructive"
          onConfirm={() => deleteMutation.mutate()}
        />
      </DangerZone>
    </div>
  );
}
