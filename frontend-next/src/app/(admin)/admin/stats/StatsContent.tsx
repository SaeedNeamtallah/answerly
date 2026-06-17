"use client";

import { useQuery } from "@tanstack/react-query";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Activity, BarChart3, Clock, Hand, HelpCircle, MessageSquare, RotateCcw } from "lucide-react";

import { getAdminOverview, getAdminStats } from "@/lib/api/admin";
import { queryKeys } from "@/lib/api/queryKeys";

import { AdminMetricCards } from "@/components/admin/AdminMetricCards";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

export default function StatsContent() {
  const statsQuery = useQuery({ queryKey: queryKeys.admin.stats, queryFn: getAdminStats });
  const overviewQuery = useQuery({ queryKey: queryKeys.admin.overview, queryFn: getAdminOverview });

  if (statsQuery.isLoading || overviewQuery.isLoading) {
    return <LoadingState label="Loading admin stats..." />;
  }

  if (statsQuery.isError || overviewQuery.isError) {
    return <ErrorState description="Failed to load admin stats." />;
  }

  const stats = statsQuery.data || {};
  const conversationTotal = Number(stats.conversations || 0);
  const escalated = Number(stats.escalated_conversations || 0);
  const open = Number(stats.open_conversations || 0);
  const resolvedOrOther = Math.max(conversationTotal - escalated - open, 0);
  const chartData = [
    { name: "Open", value: open, fill: "#818cf8" }, // indigo-400
    { name: "Escalated", value: escalated, fill: "#fbbf24" }, // amber-400
    { name: "Other", value: resolvedOrOther, fill: "#34d399" }, // emerald-400
  ].filter((item) => item.value > 0);
  const escalationRate = conversationTotal > 0 ? Math.round((escalated / conversationTotal) * 100) : 0;

  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Admin Stats</h1>
          <p className="text-sm text-slate-500 mt-1">
            Platform-wide product metrics from the admin stats endpoints.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="h-10 rounded-xl px-4 border-slate-200 text-slate-600 bg-white">
            <RotateCcw className="size-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>
      
      <AdminMetricCards overview={stats} />
      
      <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden flex flex-col">
          <div className="border-b border-slate-200 bg-slate-50/50 px-5 py-4 flex items-center justify-between">
            <h3 className="font-semibold text-slate-900 flex items-center gap-2">
              <BarChart3 className="size-4 text-indigo-500" />
              Conversation Mix
            </h3>
          </div>
          <div className="p-6 flex-1 flex flex-col">
            {chartData.length > 0 ? (
              <div className="h-64 w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Tooltip 
                      contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      itemStyle={{ color: '#0f172a', fontWeight: 500 }}
                    />
                    <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={100} paddingAngle={2}>
                      {chartData.map((entry) => (
                        <Cell key={entry.name} fill={entry.fill} stroke="transparent" />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <span className="text-3xl font-bold text-slate-900">{conversationTotal}</span>
                  <span className="text-xs text-slate-500 font-medium uppercase tracking-wider">Total</span>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center space-y-3">
                <div className="flex size-12 items-center justify-center rounded-full bg-slate-50 text-slate-400">
                  <HelpCircle className="size-6" />
                </div>
                <div>
                  <p className="font-medium text-slate-900">No conversations</p>
                  <p className="text-sm text-slate-500 mt-1">No conversations have been recorded yet.</p>
                </div>
              </div>
            )}
            
            {chartData.length > 0 && (
              <div className="mt-6 grid grid-cols-3 gap-2 text-center">
                {chartData.map(item => (
                  <div key={item.name} className="flex flex-col items-center">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="size-2.5 rounded-full" style={{ backgroundColor: item.fill }} />
                      <span className="text-xs text-slate-500 font-medium">{item.name}</span>
                    </div>
                    <span className="text-lg font-semibold text-slate-900">{item.value}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden flex flex-col">
          <div className="border-b border-slate-200 bg-slate-50/50 px-5 py-4 flex items-center justify-between">
            <h3 className="font-semibold text-slate-900 flex items-center gap-2">
              <Activity className="size-4 text-emerald-500" />
              Operational Ratios
            </h3>
          </div>
          <div className="p-6 space-y-8 flex-1">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Hand className="size-4 text-amber-500" />
                  <span className="font-medium text-slate-900">Escalation Rate</span>
                </div>
                <span className="font-bold text-slate-900">{escalationRate}%</span>
              </div>
              <Progress value={escalationRate} className="h-2.5 bg-slate-200" />
              <p className="mt-3 text-xs text-slate-500">
                {escalated} out of {conversationTotal} conversations required human intervention.
              </p>
            </div>
            
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm relative overflow-hidden group hover:border-indigo-200 transition-colors">
                <div className="absolute right-0 top-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
                  <MessageSquare className="size-12 text-indigo-600" />
                </div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="size-2 rounded-full bg-indigo-400" />
                  <p className="text-sm font-medium text-slate-600">Open</p>
                </div>
                <p className="text-3xl font-bold text-slate-900">{open}</p>
              </div>
              
              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm relative overflow-hidden group hover:border-amber-200 transition-colors">
                <div className="absolute right-0 top-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
                  <Hand className="size-12 text-amber-600" />
                </div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="size-2 rounded-full bg-amber-400" />
                  <p className="text-sm font-medium text-slate-600">Escalated</p>
                </div>
                <p className="text-3xl font-bold text-slate-900">{escalated}</p>
              </div>
              
              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm relative overflow-hidden group hover:border-emerald-200 transition-colors">
                <div className="absolute right-0 top-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
                  <Clock className="size-12 text-emerald-600" />
                </div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="size-2 rounded-full bg-emerald-400" />
                  <p className="text-sm font-medium text-slate-600">Messages 24h</p>
                </div>
                <p className="text-3xl font-bold text-slate-900">{Number(stats.messages_last_24h || 0)}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
