"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { askProject } from "@/lib/api/query";
import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";
import { QueryResponse } from "@/lib/types/query";

import { PageHeader } from "@/components/layout/PageHeader";
import { TestChatPanel } from "@/components/knowledge-bases/TestChatPanel";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function SmartChatPage() {
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [history, setHistory] = useState<QueryResponse[]>([]);
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    select: normalizeProjectListResponse,
  });

  const queryMutation = useMutation({
    mutationFn: (question: string) => askProject(selectedProjectId, { query: question, language: "en" }),
    onSuccess: (result) => setHistory((current) => [result, ...current]),
  });

  if (projectsQuery.isLoading) {
    return <LoadingState label="Loading projects..." />;
  }

  if (projectsQuery.isError) {
    return <ErrorState description="Failed to load project selector." />;
  }

  const projects = projectsQuery.data || [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Query"
        title="Smart Chat"
        description="This page calls the existing project query endpoint directly. No streaming endpoint is used."
      />
      {projects.length === 0 ? (
        <EmptyState title="No knowledge bases" description="Create a knowledge base before starting Smart Chat." />
      ) : (
        <>
          <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
            <SelectTrigger className="max-w-sm bg-white">
              <SelectValue placeholder="Select knowledge base" />
            </SelectTrigger>
            <SelectContent>
              {projects.map((project) => (
                <SelectItem key={project.id} value={String(project.id)}>
                  {project.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedProjectId ? (
            <TestChatPanel
              onSubmit={(question) => queryMutation.mutate(question)}
              isPending={queryMutation.isPending}
              result={history[0] || null}
            />
          ) : (
            <EmptyState title="Select a knowledge base" description="Choose one before asking questions." />
          )}
        </>
      )}
    </div>
  );
}
