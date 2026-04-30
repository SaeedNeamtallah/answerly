import Link from "next/link";

import { Project } from "@/lib/types/project";

import { DataTable } from "@/components/shared/DataTable";

export function KnowledgeBaseTable({ projects }: { projects: Project[] }) {
  return (
    <DataTable
      columns={["Name", "Description", "Open"]}
      rows={projects.map((project) => [
        project.name,
        project.description || "—",
        <Link key={project.id} href={`/knowledge-bases/${project.id}`} className="text-indigo-600">
          Details
        </Link>,
      ])}
    />
  );
}
