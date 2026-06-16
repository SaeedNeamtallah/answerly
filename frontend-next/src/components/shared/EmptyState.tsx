import Link from "next/link";
import { type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";

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
    <Empty className="min-h-48 border border-dashed border-border bg-card/80">
      <EmptyHeader>
        {icon ? <EmptyMedia variant="icon">{icon}</EmptyMedia> : null}
        <EmptyTitle>{title}</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>
      <EmptyContent>
        {actionLabel && actionHref ? (
          <Button asChild>
            <Link href={actionHref}>{actionLabel}</Link>
          </Button>
        ) : null}
        {actionLabel && action ? <Button onClick={action}>{actionLabel}</Button> : null}
      </EmptyContent>
    </Empty>
  );
}
