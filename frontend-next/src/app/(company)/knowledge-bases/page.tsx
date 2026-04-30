"use client";

import { useQuery } from "@tanstack/react-query";

import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";

import { PageHeader } from "@/components/layout/PageHeader";
import { KnowledgeBaseCard } from "@/components/knowledge-bases/KnowledgeBaseCard";
import { KnowledgeBaseFormDialog } from "@/components/knowledge-bases/KnowledgeBaseFormDialog";
import { KnowledgeBaseTable } from "@/components/knowledge-bases/KnowledgeBaseTable";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function KnowledgeBasesPage() {
  const query = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    select: normalizeProjectListResponse,
  });

  if (query.isLoading) {
    return <LoadingState label="Loading knowledge bases..." />;
  }

  if (query.isError) {
    return <ErrorState description="Failed to load knowledge bases." onRetry={() => query.refetch()} />;
  }

  const projects = query.data || [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Knowledge bases"
        title="Knowledge Bases"
        description="Backend projects are surfaced here with customer-friendly naming."
        actions={<KnowledgeBaseFormDialog />}
      />

      {projects.length === 0 ? (
        <EmptyState
          title="No knowledge bases yet"
          description="Create the first one to start uploading documents and testing retrieval."
        />
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-3">
            {projects.map((project) => (
              <KnowledgeBaseCard key={project.id} project={project} />
            ))}
          </div>
          <KnowledgeBaseTable projects={projects} />
        </>
      )}
    </div>
  );
}
