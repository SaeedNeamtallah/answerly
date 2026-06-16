"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { BotMessageSquare, Database, MessagesSquare } from "lucide-react";

import { askProject } from "@/lib/api/query";
import { queryKeys } from "@/lib/api/queryKeys";
import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";
import { QueryResponse } from "@/lib/types/query";

import { PageHeader } from "@/components/layout/PageHeader";
import { TestChatPanel } from "@/components/knowledge-bases/TestChatPanel";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { MetricCard } from "@/components/shared/MetricCard";

export default function SmartChatPage() {
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [history, setHistory] = useState<QueryResponse[]>([]);
  const projectsQuery = useQuery({
    queryKey: queryKeys.projects.all,
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
          <div className="grid gap-4 md:grid-cols-3">
            <MetricCard title="Knowledge Bases" value={projects.length} icon={<Database className="size-4" />} tone="info" />
            <MetricCard title="Questions This Session" value={history.length} icon={<MessagesSquare className="size-4" />} tone="default" />
            <MetricCard title="Selected Project" value={selectedProjectId || "None"} icon={<BotMessageSquare className="size-4" />} tone={selectedProjectId ? "success" : "warning"} />
          </div>
          <Card className="border-border/80 bg-card shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">Knowledge base selector</CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
                <SelectTrigger className="max-w-sm bg-background">
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
            </CardContent>
          </Card>
          {selectedProjectId ? (
            <TestChatPanel
              onSubmit={(question) => queryMutation.mutate(question)}
              isPending={queryMutation.isPending}
              result={history[0] || null}
            />
          ) : (
            <EmptyState title="Select a knowledge base" description="Choose one before asking questions." />
          )}
          {history.length > 1 ? (
            <Card className="border-border/80 bg-card shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Session history</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {history.slice(1).map((item, index) => (
                  <div key={`${item.answer.slice(0, 30)}-${index}`} className="rounded-lg border bg-background p-3">
                    <p className="line-clamp-3 text-sm text-muted-foreground">{item.answer}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          ) : null}
        </>
      )}
    </div>
  );
}
