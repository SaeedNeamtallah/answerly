"use client";

import { useQuery } from "@tanstack/react-query";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

import { getAdminOverview, getAdminStats } from "@/lib/api/admin";
import { queryKeys } from "@/lib/api/queryKeys";

import { AdminMetricCards } from "@/components/admin/AdminMetricCards";
import { PageHeader } from "@/components/layout/PageHeader";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Progress } from "@/components/ui/progress";

export default function AdminStatsPage() {
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
    { name: "Open", value: open, fill: "var(--chart-1)" },
    { name: "Escalated", value: escalated, fill: "var(--chart-4)" },
    { name: "Other", value: resolvedOrOther, fill: "var(--chart-3)" },
  ].filter((item) => item.value > 0);
  const escalationRate = conversationTotal > 0 ? Math.round((escalated / conversationTotal) * 100) : 0;

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Stats" title="Admin Stats" description="Platform-wide product metrics from the admin stats endpoints." />
      <AdminMetricCards overview={stats} />
      <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
        <Card className="border-border/80 bg-card shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">Conversation Mix</CardTitle>
          </CardHeader>
          <CardContent>
            {chartData.length > 0 ? (
              <ChartContainer config={{ value: { label: "Conversations" } }} className="h-64 w-full">
                <ResponsiveContainer>
                  <PieChart>
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={90}>
                      {chartData.map((entry) => (
                        <Cell key={entry.name} fill={entry.fill} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </ChartContainer>
            ) : (
              <p className="text-sm text-muted-foreground">No conversations have been recorded yet.</p>
            )}
          </CardContent>
        </Card>
        <Card className="border-border/80 bg-card shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">Operational Ratios</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Escalation rate</span>
                <span className="font-medium">{escalationRate}%</span>
              </div>
              <Progress value={escalationRate} />
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg border bg-background p-3">
                <p className="text-xs text-muted-foreground">Open</p>
                <p className="text-2xl font-semibold">{open}</p>
              </div>
              <div className="rounded-lg border bg-background p-3">
                <p className="text-xs text-muted-foreground">Escalated</p>
                <p className="text-2xl font-semibold">{escalated}</p>
              </div>
              <div className="rounded-lg border bg-background p-3">
                <p className="text-xs text-muted-foreground">Messages 24h</p>
                <p className="text-2xl font-semibold">{Number(stats.messages_last_24h || 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
