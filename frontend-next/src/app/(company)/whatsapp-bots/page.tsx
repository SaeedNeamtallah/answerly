"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { CheckCircle2, AlertCircle, PowerOff, Plus, MessageSquare } from "lucide-react";

import {
  createWhatsAppIntegration,
  getWhatsAppIntegrations,
} from "@/lib/api/whatsappIntegrations";
import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";

import { WhatsAppBotFormDrawer, type BotFormValues } from "@/components/whatsapp-bots/WhatsAppBotFormDrawer";
import { WhatsAppBotTable } from "@/components/whatsapp-bots/WhatsAppBotTable";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { Button } from "@/components/ui/button";

export default function WhatsAppBotsPage() {
  const queryClient = useQueryClient();
  const botsQuery = useQuery({
    queryKey: ["whatsappIntegrations"],
    queryFn: getWhatsAppIntegrations,
  });
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    select: normalizeProjectListResponse,
  });

  const createMutation = useMutation({
    mutationFn: (values: BotFormValues) =>
      createWhatsAppIntegration({
        project_id: values.project_id,
        name: values.name,
        phone_number: values.phone_number,
        fallback_message: values.fallback_message,
        human_handoff_enabled: values.human_handoff_enabled,
        show_sources_to_customer: values.show_sources_to_customer,
      }),
    onSuccess: () => {
      toast.success("WhatsApp integration created");
      queryClient.invalidateQueries({ queryKey: ["whatsappIntegrations"] });
    },
  });

  if (botsQuery.isLoading || projectsQuery.isLoading) {
    return <LoadingState label="Loading WhatsApp bots..." />;
  }

  if (botsQuery.isError || projectsQuery.isError) {
    return <ErrorState description="Failed to load WhatsApp bots." />;
  }

  const bots = botsQuery.data || [];
  const projects = projectsQuery.data || [];

  const totalBots = bots.length;
  const onlineBots = bots.filter((b) => b.status === "active").length;
  const issueBots = bots.filter((b) => b.status === "error").length;
  const offlineBots = bots.filter((b) => b.status === "inactive" || b.status === "disabled" || b.status === "pending").length;

  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">WhatsApp Bots</h1>
          <p className="text-sm text-slate-500 mt-1">
            Connect and manage your customer-support bots powered by your knowledge bases.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <WhatsAppBotFormDrawer 
            projects={projects} 
            isPending={createMutation.isPending} 
            onSubmit={(values) => createMutation.mutate(values)} 
            trigger={
              <Button className="h-10 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm px-4">
                <Plus className="mr-2 size-4" />
                New Bot
              </Button>
            }
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="rounded-xl bg-indigo-50 p-3 text-indigo-600 ring-1 ring-indigo-100">
              <MessageSquare className="size-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Total Bots</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{totalBots}</h3>
            </div>
          </div>
        </div>
        
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="rounded-xl bg-emerald-50 p-3 text-emerald-600 ring-1 ring-emerald-100">
              <CheckCircle2 className="size-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Online</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{onlineBots}</h3>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="rounded-xl bg-amber-50 p-3 text-amber-600 ring-1 ring-amber-100">
              <AlertCircle className="size-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">With Issues</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{issueBots}</h3>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="rounded-xl bg-slate-100 p-3 text-slate-500 ring-1 ring-slate-200">
              <PowerOff className="size-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Offline/Pending</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{offlineBots}</h3>
            </div>
          </div>
        </div>
      </div>

      {bots.length === 0 ? (
        <EmptyState title="No WhatsApp bots" description="Create the first integration when you are ready." />
      ) : (
        <div className="space-y-6">
          <WhatsAppBotTable bots={bots} projects={projects} />
        </div>
      )}
    </div>
  );
}
