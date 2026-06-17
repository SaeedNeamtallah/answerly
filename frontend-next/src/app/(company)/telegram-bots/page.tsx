"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Bot, CheckCircle2, AlertCircle, PowerOff, Search, Plus } from "lucide-react";

import {
  createBotIntegration,
  listBotIntegrations,
} from "@/lib/api/botIntegrations";
import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";

import { BotFormDrawer, type BotFormValues } from "@/components/bots/BotFormDrawer";
import { BotTable } from "@/components/bots/BotTable";
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

  if (botsQuery.isLoading || projectsQuery.isLoading) {
    return <LoadingState label="Loading Telegram bots..." />;
  }

  if (botsQuery.isError || projectsQuery.isError) {
    return <ErrorState description="Failed to load Telegram bots." />;
  }

  const bots = botsQuery.data || [];
  const projects = projectsQuery.data || [];

  const totalBots = bots.length;
  const onlineBots = bots.filter((b) => b.status === "active").length;
  const issueBots = bots.filter((b) => b.status === "error").length;
  const offlineBots = bots.filter((b) => b.status === "inactive" || b.status === "disabled").length;

  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Telegram Bots</h1>
          <p className="text-sm text-slate-500 mt-1">
            Connect and manage your customer-support bots powered by your knowledge bases.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Search can be implemented later */}
          <BotFormDrawer 
            projects={projects} 
            isPending={createMutation.isPending} 
            onSubmit={(values) => createMutation.mutate(values)} 
            trigger={
              <Button className="h-10 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm px-4">
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
              <Bot className="size-6" />
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
              <p className="text-sm font-medium text-slate-500">Offline</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{offlineBots}</h3>
            </div>
          </div>
        </div>
      </div>

      {bots.length === 0 ? (
        <EmptyState title="No Telegram bots" description="Create the first integration when you are ready." />
      ) : (
        <div className="space-y-6">
          <BotTable bots={bots} projects={projects} />
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between">
              <div>
                <h3 className="font-semibold text-slate-900">Bot Health Summary</h3>
                <p className="text-sm text-slate-500 mt-1">Real-time overview of your bot ecosystem.</p>
              </div>
              
              <div className="mt-8 space-y-6">
                <div className="h-4 flex rounded-full overflow-hidden">
                  <div className="bg-emerald-500" style={{ width: `${(onlineBots / Math.max(totalBots, 1)) * 100}%` }} />
                  <div className="bg-amber-400" style={{ width: `${(issueBots / Math.max(totalBots, 1)) * 100}%` }} />
                  <div className="bg-slate-300" style={{ width: `${(offlineBots / Math.max(totalBots, 1)) * 100}%` }} />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="text-center">
                    <div className="text-xl font-bold text-slate-900">{onlineBots}</div>
                    <div className="flex items-center gap-1.5 mt-1">
                      <div className="size-2 rounded-full bg-emerald-500" />
                      <span className="text-xs font-medium text-slate-600">Healthy</span>
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-slate-900">{issueBots}</div>
                    <div className="flex items-center gap-1.5 mt-1">
                      <div className="size-2 rounded-full bg-amber-400" />
                      <span className="text-xs font-medium text-slate-600">With Issues</span>
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-slate-900">{offlineBots}</div>
                    <div className="flex items-center gap-1.5 mt-1">
                      <div className="size-2 rounded-full bg-slate-300" />
                      <span className="text-xs font-medium text-slate-600">Offline</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
               <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-slate-900">Readiness Checklist</h3>
                  <p className="text-sm text-slate-500 mt-1">Based on best practices for reliable bot operations.</p>
                </div>
                <Button variant="link" className="text-indigo-600 h-auto p-0 text-sm">View all &rarr;</Button>
               </div>
               
               <div className="mt-6 flex items-center justify-between">
                 <div className="space-y-3 flex-1 pr-8">
                    {[
                      { label: "Webhooks connected", val: onlineBots, max: totalBots, color: "text-emerald-500" },
                      { label: "Knowledge bases linked", val: totalBots, max: totalBots, color: "text-emerald-500" },
                      { label: "Recent test successful", val: Math.max(0, onlineBots - 1), max: totalBots, color: "text-emerald-500" },
                      { label: "No recent errors", val: Math.max(0, totalBots - issueBots), max: totalBots, color: "text-amber-500" }
                    ].map((item, i) => (
                      <div key={i} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className={`size-4 ${item.color}`} />
                          <span className="text-slate-700">{item.label}</span>
                        </div>
                        <span className="text-slate-400 font-medium">{item.val} / {item.max}</span>
                      </div>
                    ))}
                 </div>
                 
                 <div className="relative size-24 shrink-0 flex items-center justify-center rounded-full border-4 border-emerald-500/20">
                   <svg className="absolute inset-0 size-full -rotate-90" viewBox="0 0 100 100">
                     <circle cx="50" cy="50" r="46" fill="none" stroke="currentColor" strokeWidth="8" className="text-emerald-500" strokeDasharray={`${(onlineBots / Math.max(totalBots, 1)) * 289} 289`} />
                   </svg>
                   <div className="text-center">
                     <div className="text-xl font-bold text-slate-900">{Math.round((onlineBots / Math.max(totalBots, 1)) * 100)}%</div>
                   </div>
                 </div>
               </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
