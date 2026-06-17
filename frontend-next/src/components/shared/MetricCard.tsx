import { type ReactNode } from "react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export function MetricCard({
  title,
  value,
  icon,
  hint,
  trend,
  trendDirection,
  tone = "default",
}: {
  title: string;
  value: ReactNode;
  icon?: ReactNode;
  hint?: string;
  trend?: string;
  trendDirection?: "up" | "down" | "neutral";
  tone?: "default" | "success" | "warning" | "danger" | "info" | "purple";
}) {
  const toneClass = {
    default: "bg-blue-50 text-blue-500",
    success: "bg-emerald-50 text-emerald-500",
    warning: "bg-orange-50 text-orange-500",
    danger: "bg-rose-50 text-rose-500",
    info: "bg-cyan-50 text-cyan-500",
    purple: "bg-purple-50 text-purple-500",
  }[tone];

  const isPositiveTrend = trendDirection === "up" || (trendDirection === "down" && tone === "danger");
  const trendColor = isPositiveTrend ? "text-emerald-500" : "text-rose-500";
  const TrendIcon = trendDirection === "up" ? ArrowUpRight : ArrowDownRight;

  return (
    <div className="flex flex-col rounded-2xl border border-slate-100 bg-white p-5 shadow-[0_2px_10px_rgba(0,0,0,0.02)] transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between">
        {icon ? (
          <div className={cn("flex size-14 items-center justify-center rounded-2xl", toneClass)}>
            <div className="[&>svg]:size-6">{icon}</div>
          </div>
        ) : null}
        <div className="flex flex-col items-end gap-1">
          <span className="text-sm font-medium text-slate-500">{title}</span>
          <span className="text-3xl font-bold tracking-tight text-slate-900">{value}</span>
        </div>
      </div>
      {(trend || hint) && (
        <div className="mt-5 flex items-center gap-1.5 text-xs font-medium">
          {trend ? (
            <div className={cn("flex items-center gap-0.5", trendColor)}>
              {trendDirection !== "neutral" && <TrendIcon className="size-3.5" />}
              <span>{trend}</span>
            </div>
          ) : null}
          <span className="text-slate-400">{hint || "vs yesterday"}</span>
        </div>
      )}
    </div>
  );
}
