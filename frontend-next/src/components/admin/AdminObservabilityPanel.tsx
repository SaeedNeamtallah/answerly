"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Database, ExternalLink, Gauge, MonitorDot, RefreshCw, Server } from "lucide-react";

import { getAdminObservabilityDashboards, getAdminObservabilitySummary } from "@/lib/api/admin";
import { queryKeys } from "@/lib/api/queryKeys";
import type { AdminObservabilityDashboard, AdminObservabilityMetric } from "@/lib/types/admin";
import { formatNumber, titleCase } from "@/lib/utils/formatters";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MetricCard } from "@/components/shared/MetricCard";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { cn } from "@/lib/utils/cn";

const ranges = ["1h", "6h", "24h", "7d"] as const;

function formatMetricValue(metric?: AdminObservabilityMetric) {
  if (!metric || metric.value === null || metric.value === undefined || Number.isNaN(metric.value)) {
    return "Unavailable";
  }

  if (metric.unit === "seconds") {
    if (metric.value < 1) {
      return `${Math.round(metric.value * 1000)} ms`;
    }
    return `${metric.value.toFixed(2)} s`;
  }

  if (metric.unit === "requests_per_second") {
    return `${metric.value.toFixed(2)}/s`;
  }

  return formatNumber(Math.round(metric.value));
}

function metricTone(metric?: AdminObservabilityMetric): "default" | "success" | "warning" | "danger" | "info" {
  if (!metric || metric.status !== "ready") {
    return "warning";
  }

  if (metric.key.includes("5xx") || metric.key.includes("failures")) {
    return Number(metric.value || 0) > 0 ? "danger" : "success";
  }

  return "info";
}

function dashboardIcon(category: string) {
  if (category === "database") {
    return <Database className="size-4" />;
  }
  if (category === "infrastructure") {
    return <Server className="size-4" />;
  }
  if (category === "api") {
    return <Activity className="size-4" />;
  }
  return <MonitorDot className="size-4" />;
}

function findMetric(metrics: AdminObservabilityMetric[] | undefined, key: string) {
  return (metrics || []).find((metric) => metric.key === key);
}

export function AdminObservabilityPanel() {
  const [range, setRange] = useState<(typeof ranges)[number]>("1h");
  const [activeDashboard, setActiveDashboard] = useState<string>("");

  const dashboardsQuery = useQuery({
    queryKey: queryKeys.admin.observabilityDashboards(range),
    queryFn: () => getAdminObservabilityDashboards(range),
  });
  const summaryQuery = useQuery({
    queryKey: queryKeys.admin.observabilitySummary(range),
    queryFn: () => getAdminObservabilitySummary(range),
    refetchInterval: 30000,
  });

  const dashboards = useMemo(() => dashboardsQuery.data || [], [dashboardsQuery.data]);
  const active = dashboards.find((dashboard) => dashboard.uid === activeDashboard) || dashboards[0];
  const metrics = summaryQuery.data?.metrics || [];
  const keyMetrics = [
    findMetric(metrics, "backend_request_rate"),
    findMetric(metrics, "backend_p95_latency"),
    findMetric(metrics, "backend_5xx_rate"),
    findMetric(metrics, "query_failures"),
  ];

  function refreshAll() {
    dashboardsQuery.refetch();
    summaryQuery.refetch();
  }

  if (dashboardsQuery.isLoading || summaryQuery.isLoading) {
    return <LoadingState label="Loading observability dashboards..." />;
  }

  if (dashboardsQuery.isError || summaryQuery.isError) {
    return <ErrorState description="Failed to load observability data from the backend." />;
  }

  if (!dashboards.length) {
    return <EmptyState title="No dashboards configured" description="No Grafana dashboards were returned by the admin observability API." />;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {keyMetrics.map((metric) => (
          <MetricCard
            key={metric?.key || "missing"}
            title={metric?.label || "Metric"}
            value={formatMetricValue(metric)}
            hint={metric?.description}
            tone={metricTone(metric)}
            icon={<Gauge className="size-4" />}
          />
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
        <Card className="border-border/80 shadow-sm">
          <CardHeader className="gap-4 border-b bg-muted/30">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-base">
                  <MonitorDot className="size-4 text-primary" />
                  {active?.title || "Observability Dashboard"}
                </CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">{active?.description}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Tabs value={active?.uid} onValueChange={setActiveDashboard}>
                  <TabsList className="flex-wrap">
                    {dashboards.map((dashboard) => (
                      <TabsTrigger key={dashboard.uid} value={dashboard.uid} className="gap-1.5">
                        {dashboardIcon(dashboard.category)}
                        <span className="hidden sm:inline">{titleCase(dashboard.category)}</span>
                      </TabsTrigger>
                    ))}
                  </TabsList>
                </Tabs>
              </div>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap gap-2">
                {ranges.map((item) => (
                  <Button
                    key={item}
                    type="button"
                    size="sm"
                    variant={range === item ? "default" : "outline"}
                    onClick={() => setRange(item)}
                  >
                    {item}
                  </Button>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Button type="button" size="sm" variant="outline" onClick={refreshAll}>
                  <RefreshCw className="size-3.5" />
                  Refresh
                </Button>
                {active ? (
                  <Button asChild size="sm" variant="outline">
                    <a href={active.url} target="_blank" rel="noreferrer">
                      <ExternalLink className="size-3.5" />
                      Open Grafana
                    </a>
                  </Button>
                ) : null}
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {active?.embed_url ? (
              <div className="h-[680px] min-h-[560px] bg-background">
                <iframe
                  key={`${active.uid}-${range}`}
                  title={active.title}
                  src={active.embed_url}
                  className="h-full w-full border-0"
                  loading="lazy"
                />
              </div>
            ) : (
              <div className="p-4">
                <Alert>
                  <MonitorDot className="size-4" />
                  <AlertTitle>Grafana embedding is disabled</AlertTitle>
                  <AlertDescription>
                    The backend returned dashboard links only. Use the approved Grafana link above or enable embedding in the monitoring configuration.
                  </AlertDescription>
                </Alert>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className="border-border/80 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">Monitoring Services</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between gap-3 rounded-lg border bg-background p-3">
                <div>
                  <p className="text-sm font-medium">Grafana</p>
                  <p className="text-xs text-muted-foreground">
                    {summaryQuery.data?.grafana.version ? `v${summaryQuery.data.grafana.version}` : "Dashboard renderer"}
                  </p>
                </div>
                <StatusBadge status={summaryQuery.data?.grafana.status} />
              </div>
              <div className="flex items-center justify-between gap-3 rounded-lg border bg-background p-3">
                <div>
                  <p className="text-sm font-medium">Prometheus</p>
                  <p className="text-xs text-muted-foreground">Metrics source</p>
                </div>
                <StatusBadge status={summaryQuery.data?.prometheus.status} />
              </div>
              <Badge variant="outline" className="rounded-md">
                Updated {summaryQuery.data?.generated_at ? new Date(summaryQuery.data.generated_at).toLocaleTimeString() : "now"}
              </Badge>
            </CardContent>
          </Card>

          <Card className="border-border/80 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">Prometheus Targets</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(summaryQuery.data?.targets || []).map((target) => (
                <div key={target.job} className="rounded-lg border bg-background p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium">{target.label}</p>
                      <p className="text-xs text-muted-foreground">{target.job}</p>
                    </div>
                    <StatusBadge status={target.health} />
                  </div>
                  {target.last_error ? <p className="mt-2 text-xs text-destructive">{target.last_error}</p> : null}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border/80 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">Dashboard Catalog</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {dashboards.map((dashboard: AdminObservabilityDashboard) => (
                <button
                  key={dashboard.uid}
                  type="button"
                  onClick={() => setActiveDashboard(dashboard.uid)}
                  className={cn(
                    "flex w-full items-start gap-3 rounded-lg border bg-background p-3 text-left transition-colors hover:bg-muted/60",
                    active?.uid === dashboard.uid && "border-primary/40 bg-primary/5",
                  )}
                >
                  <span className="mt-0.5 flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    {dashboardIcon(dashboard.category)}
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium">{dashboard.title}</span>
                    <span className="mt-1 block text-xs text-muted-foreground">{dashboard.description}</span>
                  </span>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
