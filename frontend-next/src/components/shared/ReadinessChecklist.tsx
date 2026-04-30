import { CheckCircle2, CircleDashed, XCircle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function getCheckStateIcon(value: unknown) {
  if (value === true || String(value).toLowerCase() === "ready") {
    return <CheckCircle2 className="size-4 text-emerald-600" />;
  }

  if (value === false || String(value).toLowerCase() === "failed") {
    return <XCircle className="size-4 text-rose-600" />;
  }

  return <CircleDashed className="size-4 text-slate-400" />;
}

export function ReadinessChecklist({
  title,
  checks,
}: {
  title: string;
  checks?: Record<string, unknown>;
}) {
  const entries = Object.entries(checks || {});

  return (
    <Card className="border-slate-200">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {entries.length === 0 ? (
          <p className="text-sm text-slate-500">No readiness checks returned yet.</p>
        ) : (
          entries.map(([key, value]) => (
            <div key={key} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 px-3 py-2">
              <span className="text-sm font-medium text-slate-700">{key.replace(/_/g, " ")}</span>
              <div className="flex items-center gap-2 text-sm text-slate-500">
                {getCheckStateIcon(value)}
                <span>{typeof value === "object" ? JSON.stringify(value) : String(value)}</span>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
