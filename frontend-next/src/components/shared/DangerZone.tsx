import { type ReactNode } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function DangerZone({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <Card className="border-rose-200 bg-rose-50/60 shadow-sm">
      <CardHeader>
        <CardTitle className="text-rose-700">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-rose-700/80">{description}</p>
        {children}
      </CardContent>
    </Card>
  );
}
