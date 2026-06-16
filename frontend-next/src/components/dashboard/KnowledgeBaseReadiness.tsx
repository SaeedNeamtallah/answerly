import { BotIntegration } from "@/lib/types/bot";
import { Project } from "@/lib/types/project";

import { EmptyState } from "@/components/shared/EmptyState";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function KnowledgeBaseReadiness({ projects, bots }: { projects: Project[]; bots: BotIntegration[] }) {
  if (projects.length === 0) {
    return (
      <EmptyState
        title="Create your first knowledge base"
        description="Projects from the backend are presented here as customer-facing knowledge bases."
        actionLabel="Create knowledge base"
        actionHref="/knowledge-bases"
      />
    );
  }

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Knowledge base readiness</CardTitle>
        <CardDescription>Backend projects with linked bot coverage from integration records.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {projects.slice(0, 5).map((project) => {
          const linkedBots = bots.filter((bot) => bot.project_id === project.id).length;
          return (
            <div key={project.id} className="grid gap-3 rounded-xl border border-border px-3 py-3 sm:grid-cols-[1fr_auto] sm:items-center">
              <div className="min-w-0">
                <p className="truncate font-medium text-foreground">{project.name}</p>
                <p className="truncate text-sm text-muted-foreground">{project.description || "No description provided."}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">{linkedBots} linked bots</span>
                <StatusBadge status={linkedBots > 0 ? "ready" : "attention"} />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
