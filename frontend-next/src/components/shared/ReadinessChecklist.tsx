import { CheckCircle2, CircleDashed, ShieldCheck, XCircle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

function getCheckStateIcon(value: unknown) {
  if (value === true || String(value).toLowerCase() === "ready") {
    return <CheckCircle2 className="size-4 text-emerald-600" />;
  }

  if (value === false || String(value).toLowerCase() === "failed") {
    return <XCircle className="size-4 text-rose-600" />;
  }

    return <CircleDashed className="size-4 text-muted-foreground" />;
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
    <Card className="border-border/80 bg-card shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <span className="flex size-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-700">
            <ShieldCheck className="size-4" />
          </span>
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">No readiness checks returned yet.</p>
        ) : (
          entries.map(([key, value]) => (
            <div key={key} className="flex items-center justify-between gap-3 rounded-xl border bg-background px-3 py-2">
              <span className="text-sm font-medium capitalize text-foreground">{key.replace(/_/g, " ")}</span>
              <Badge variant="outline" className="h-auto gap-2 rounded-md py-1 text-muted-foreground">
                {getCheckStateIcon(value)}
                <span>{typeof value === "object" ? JSON.stringify(value) : String(value)}</span>
              </Badge>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
