import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ErrorState({
  title = "Something went wrong",
  description,
  retryLabel = "Try again",
  onRetry,
}: {
  title?: string;
  description: string;
  retryLabel?: string;
  onRetry?: () => void;
}) {
  return (
    <Card className="border-rose-200 bg-rose-50/70">
      <CardHeader className="flex flex-row items-center gap-3">
        <AlertTriangle className="size-5 text-rose-600" />
        <CardTitle className="text-rose-700">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm text-rose-700">
        <p>{description}</p>
        {onRetry ? (
          <Button variant="outline" onClick={onRetry}>
            {retryLabel}
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}
