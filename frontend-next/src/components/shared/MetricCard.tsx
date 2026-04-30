import { type ReactNode } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function MetricCard({
  title,
  value,
  icon,
  hint,
}: {
  title: string;
  value: ReactNode;
  icon?: ReactNode;
  hint?: string;
}) {
  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-sm font-medium text-slate-600">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-semibold tracking-tight text-slate-950">{value}</div>
        {hint ? <p className="mt-2 text-sm text-slate-500">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}
