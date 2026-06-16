import Link from "next/link";
import { CheckCircle2, CircleDashed, MessageSquareText } from "lucide-react";

import { BotIntegration } from "@/lib/types/bot";
import { Conversation } from "@/lib/types/conversation";
import { Project } from "@/lib/types/project";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export function SetupChecklist({
  projects = [],
  bots = [],
  conversations = [],
}: {
  projects?: Project[];
  bots?: BotIntegration[];
  conversations?: Conversation[];
}) {
  const steps = [
    { label: "Create your first knowledge base", href: "/knowledge-bases", done: projects.length > 0 },
    { label: "Connect a Telegram bot", href: "/telegram-bots", done: bots.length > 0 },
    { label: "Review customer conversations", href: "/conversations", done: conversations.length > 0 },
    { label: "Test retrieval in Smart Chat", href: "/smart-chat", done: projects.length > 0 },
  ];
  const completed = steps.filter((step) => step.done).length;
  const percent = Math.round((completed / steps.length) * 100);

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle>Setup checklist</CardTitle>
            <CardDescription>Backend-connected steps for getting the workspace live.</CardDescription>
          </div>
          <span className="rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
            {completed} / {steps.length} complete
          </span>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <Progress value={percent} />
        {steps.map((step) => (
          <div key={step.label} className="flex items-center justify-between gap-3 rounded-xl border border-border px-3 py-3">
            <div className="flex items-center gap-3">
              {step.done ? (
                <CheckCircle2 className="size-4 text-emerald-600" />
              ) : (
                <CircleDashed className="size-4 text-muted-foreground" />
              )}
              <span className="text-sm font-medium text-foreground">{step.label}</span>
            </div>
            <Button asChild size="sm" variant="outline">
              <Link href={step.href}>Open</Link>
            </Button>
          </div>
        ))}
        <div className="flex items-center gap-3 rounded-xl bg-muted px-3 py-3 text-sm text-muted-foreground">
          <MessageSquareText className="size-4 text-primary" />
          Every status here is derived from currently loaded backend resources.
        </div>
      </CardContent>
    </Card>
  );
}
