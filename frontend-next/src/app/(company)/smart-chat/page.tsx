"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { BotMessageSquare, Database, MessagesSquare, Settings2, RotateCcw } from "lucide-react";

import { askProject } from "@/lib/api/query";
import { queryKeys } from "@/lib/api/queryKeys";
import { listProjects, normalizeProjectListResponse } from "@/lib/api/projects";
import { QueryResponse } from "@/lib/types/query";

import { TestChatPanel } from "@/components/knowledge-bases/TestChatPanel";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";

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
    <div className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Smart Chat</h1>
          <p className="text-sm text-slate-500 mt-1">
            Test your knowledge base queries to ensure high quality answers.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="h-10 rounded-xl px-4 border-slate-200 text-slate-600 bg-white" onClick={() => setHistory([])}>
            <RotateCcw className="size-4 mr-2" />
            Clear History
          </Button>
          <Button className="h-10 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm px-4">
            <Settings2 className="mr-2 size-4" />
            Settings
          </Button>
        </div>
      </div>

      {projects.length === 0 ? (
        <EmptyState title="No knowledge bases" description="Create a knowledge base before starting Smart Chat." />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_320px] items-start">
          <div className="flex flex-col gap-6">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Database className="size-4 text-indigo-500" />
                Knowledge Base Selector
              </h3>
              <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
                <SelectTrigger className="w-full h-12 rounded-xl bg-slate-50/50 border-slate-200">
                  <SelectValue placeholder="Select knowledge base to test..." />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((project) => (
                    <SelectItem key={project.id} value={String(project.id)}>
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedProjectId ? (
              <TestChatPanel
                onSubmit={(question) => queryMutation.mutate(question)}
                isPending={queryMutation.isPending}
                result={history[0] || null}
              />
            ) : (
              <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-12 text-center border-dashed">
                <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-white shadow-sm border border-slate-100 mb-4">
                  <BotMessageSquare className="size-5 text-slate-400" />
                </div>
                <h3 className="text-sm font-medium text-slate-900">No knowledge base selected</h3>
                <p className="mt-1 text-sm text-slate-500">Select a knowledge base above to start testing queries.</p>
              </div>
            )}
          </div>

          <div className="flex flex-col gap-6 sticky top-6">
            <div className="grid grid-cols-2 lg:grid-cols-1 gap-4">
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-3 text-slate-500 mb-2">
                  <div className="rounded-lg bg-indigo-50 p-1.5 text-indigo-600">
                    <Database className="size-4" />
                  </div>
                  <h3 className="text-xs font-medium">Knowledge Bases</h3>
                </div>
                <div className="text-2xl font-bold text-slate-900">{projects.length}</div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-3 text-slate-500 mb-2">
                  <div className="rounded-lg bg-emerald-50 p-1.5 text-emerald-600">
                    <MessagesSquare className="size-4" />
                  </div>
                  <h3 className="text-xs font-medium">Session Queries</h3>
                </div>
                <div className="text-2xl font-bold text-slate-900">{history.length}</div>
              </div>
            </div>

            {history.length > 1 && (
              <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                <div className="border-b border-slate-200 bg-slate-50/50 px-5 py-4 flex items-center justify-between">
                  <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                    <RotateCcw className="size-4 text-indigo-500" />
                    Session History
                  </h3>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-600">
                    {history.length - 1} Previous
                  </span>
                </div>
                <div className="p-2 max-h-[400px] overflow-y-auto custom-scrollbar">
                  {history.slice(1).map((item, index) => (
                    <div key={`${item.answer.slice(0, 30)}-${index}`} className="group p-3 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer border border-transparent hover:border-slate-100">
                      <p className="line-clamp-2 text-sm text-slate-600 leading-relaxed">{item.answer}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
