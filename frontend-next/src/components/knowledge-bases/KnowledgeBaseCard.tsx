import Link from "next/link";

import { Project } from "@/lib/types/project";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

export function KnowledgeBaseCard({ project }: { project: Project }) {
  return (
    <Card className="border-slate-200">
      <CardHeader>
        <CardTitle>{project.name}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-slate-600">
        {project.description || "No description provided."}
      </CardContent>
      <CardFooter className="justify-between">
        <span className="text-xs text-slate-500">ID #{project.id}</span>
        <Button asChild size="sm">
          <Link href={`/knowledge-bases/${project.id}`}>Open</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
