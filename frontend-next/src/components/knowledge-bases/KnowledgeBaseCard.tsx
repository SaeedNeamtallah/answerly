import Link from "next/link";
import { Database, ExternalLink, FileText } from "lucide-react";

import { Project } from "@/lib/types/project";
import { formatRelativeDate } from "@/lib/utils/dates";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

export function KnowledgeBaseCard({ project }: { project: Project }) {
  return (
    <Card className="border-border/80 bg-card shadow-sm transition-shadow hover:shadow-md">
      <CardHeader className="gap-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Database className="size-4" />
          </div>
          <Badge variant="outline" className="rounded-md">
            ID #{project.id}
          </Badge>
        </div>
        <CardTitle className="line-clamp-2">{project.name}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm text-muted-foreground">
        <p className="line-clamp-3 min-h-12">{project.description || "No description provided."}</p>
        <div className="flex items-center gap-2 text-xs">
          <FileText className="size-3.5" />
          <span>Updated {formatRelativeDate(project.updated_at || project.created_at)}</span>
        </div>
      </CardContent>
      <CardFooter className="justify-between">
        <span className="text-xs text-muted-foreground">Project-backed retrieval</span>
        <Button asChild size="sm" variant="outline">
          <Link href={`/knowledge-bases/${project.id}`}>
            <ExternalLink className="size-3.5" />
            Open
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
