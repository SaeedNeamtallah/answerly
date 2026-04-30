import Link from "next/link";
import { CheckCircle2, CircleDashed } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const steps = [
  { label: "Create a knowledge base", href: "/knowledge-bases" },
  { label: "Upload documents and process them", href: "/knowledge-bases" },
  { label: "Test retrieval in Smart Chat", href: "/smart-chat" },
  { label: "Connect a Telegram bot", href: "/telegram-bots" },
];

export function SetupChecklist() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Setup checklist</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {steps.map((step) => (
          <div key={step.label} className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-3">
            <div className="flex items-center gap-3">
              <CircleDashed className="size-4 text-slate-400" />
              <span className="text-sm font-medium text-slate-700">{step.label}</span>
            </div>
            <Button asChild size="sm" variant="outline">
              <Link href={step.href}>Open</Link>
            </Button>
          </div>
        ))}
        <div className="flex items-center gap-3 rounded-xl bg-emerald-50 px-3 py-3 text-sm text-emerald-700">
          <CheckCircle2 className="size-4" />
          Company onboarding remains fully backend-driven. This frontend keeps the existing API flow.
        </div>
      </CardContent>
    </Card>
  );
}
