import Link from "next/link";
import { type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function EmptyState({
  title,
  description,
  actionLabel,
  actionHref,
  action,
  icon,
}: {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  action?: () => void;
  icon?: ReactNode;
}) {
  return (
    <Card className="border-dashed border-slate-300 bg-white/80">
      <CardHeader className="items-start gap-3">
        {icon}
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm text-slate-600">
        <p>{description}</p>
        {actionLabel && actionHref ? (
          <Button asChild>
            <Link href={actionHref}>{actionLabel}</Link>
          </Button>
        ) : null}
        {actionLabel && action ? <Button onClick={action}>{actionLabel}</Button> : null}
      </CardContent>
    </Card>
  );
}
