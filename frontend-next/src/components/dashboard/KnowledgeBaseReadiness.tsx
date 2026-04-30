import { Project } from "@/lib/types/project";

import { EmptyState } from "@/components/shared/EmptyState";

export function KnowledgeBaseReadiness({ projects }: { projects: Project[] }) {
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
    <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-950">Knowledge base readiness</h3>
      {projects.slice(0, 5).map((project) => (
        <div key={project.id} className="rounded-xl border border-slate-200 px-3 py-3">
          <p className="font-medium text-slate-900">{project.name}</p>
          <p className="text-sm text-slate-500">{project.description || "No description provided."}</p>
        </div>
      ))}
    </div>
  );
}
