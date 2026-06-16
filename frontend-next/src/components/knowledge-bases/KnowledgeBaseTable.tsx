import Link from "next/link";
import { ExternalLink } from "lucide-react";

import { Project } from "@/lib/types/project";
import { formatRelativeDate } from "@/lib/utils/dates";

import { DataTable } from "@/components/shared/DataTable";
import { Button } from "@/components/ui/button";

export function KnowledgeBaseTable({ projects }: { projects: Project[] }) {
  return (
    <DataTable
      caption="Knowledge base inventory"
      columns={["Name", "Description", "Updated", "Open"]}
      rows={projects.map((project) => [
        project.name,
        project.description || "—",
        formatRelativeDate(project.updated_at || project.created_at),
        <Button key={project.id} asChild size="sm" variant="outline">
          <Link href={`/knowledge-bases/${project.id}`}>
            <ExternalLink className="size-3.5" />
            Details
          </Link>
        </Button>,
      ])}
    />
  );
}
