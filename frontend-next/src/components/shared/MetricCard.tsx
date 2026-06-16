import { type ReactNode } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils/cn";

export function MetricCard({
  title,
  value,
  icon,
  hint,
  trend,
  tone = "default",
}: {
  title: string;
  value: ReactNode;
  icon?: ReactNode;
  hint?: string;
  trend?: ReactNode;
  tone?: "default" | "success" | "warning" | "danger" | "info";
}) {
  const toneClass = {
    default: "bg-primary/10 text-primary",
    success: "bg-emerald-500/10 text-emerald-700",
    warning: "bg-amber-500/10 text-amber-700",
    danger: "bg-rose-500/10 text-rose-700",
    info: "bg-cyan-500/10 text-cyan-700",
  }[tone];

  return (
    <Card className="border-border/80 bg-card shadow-sm transition-shadow hover:shadow-md">
      <CardHeader className="flex flex-row items-start justify-between gap-3 pb-1">
        <CardTitle className="text-xs font-medium text-muted-foreground">{title}</CardTitle>
        {icon ? <div className={cn("flex size-10 items-center justify-center rounded-xl", toneClass)}>{icon}</div> : null}
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="text-3xl font-semibold tracking-tight text-foreground">{value}</div>
        {trend || hint ? (
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            {trend ? <span className="font-medium text-emerald-600">{trend}</span> : null}
            {hint ? <span>{hint}</span> : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
