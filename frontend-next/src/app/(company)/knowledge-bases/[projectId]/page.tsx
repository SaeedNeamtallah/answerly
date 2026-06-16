"use client";

import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Boxes, Database, FileText, RefreshCw, UploadCloud } from "lucide-react";

import { listBotIntegrations } from "@/lib/api/botIntegrations";
import {
  deleteDocument,
  getTask,
  listDocuments,
  processAndIndexDocument,
  processDocument,
  uploadDocument,
} from "@/lib/api/documents";
import { askProject } from "@/lib/api/query";
import { getProject, getProjectStats, reindexProject } from "@/lib/api/projects";
import { DocumentAsset, TaskStatusResponse } from "@/lib/types/document";

import { PageHeader } from "@/components/layout/PageHeader";
import { DocumentsTable } from "@/components/knowledge-bases/DocumentsTable";
import { LinkedBotsPanel } from "@/components/knowledge-bases/LinkedBotsPanel";
import { TestChatPanel } from "@/components/knowledge-bases/TestChatPanel";
import { UploadDocumentCard } from "@/components/knowledge-bases/UploadDocumentCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { MetricCard } from "@/components/shared/MetricCard";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatBytes, formatNumber } from "@/lib/utils/formatters";

export default function KnowledgeBaseDetailPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const queryClient = useQueryClient();

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
  });
  const statsQuery = useQuery({
    queryKey: ["projectStats", projectId],
    queryFn: () => getProjectStats(projectId),
  });
  const documentsQuery = useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => listDocuments(projectId),
  });
  const botsQuery = useQuery({
    queryKey: ["botIntegrations"],
    queryFn: listBotIntegrations,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(projectId, file),
    onSuccess: () => {
      toast.success("Document uploaded");
      queryClient.invalidateQueries({ queryKey: ["documents", projectId] });
    },
  });

  const [taskState, setTaskState] = useState<TaskStatusResponse | null>(null);
  const [chatResult, setChatResult] = useState<Awaited<ReturnType<typeof askProject>> | null>(null);

  const actionMutation = useMutation({
    mutationFn: async ({
      type,
      document,
    }: {
      type: "process" | "processAndIndex" | "delete";
      document: DocumentAsset;
    }) => {
      if (type === "process") {
        return processDocument(document.id);
      }
      if (type === "processAndIndex") {
        return processAndIndexDocument(document.id);
      }
      await deleteDocument(document.id);
      return null;
    },
    onSuccess: async (result, variables) => {
      queryClient.invalidateQueries({ queryKey: ["documents", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projectStats", projectId] });
      if (variables.type === "delete") {
        toast.success("Document deleted");
        return;
      }
      if (result?.task_id) {
        const task = await getTask(result.task_id);
        setTaskState(task);
        toast.success(`Task ${task.task_id} queued`);
      }
    },
  });

  const reindexMutation = useMutation({
    mutationFn: () => reindexProject(projectId),
    onSuccess: async (result) => {
      const task = await getTask(result.task_id);
      setTaskState(task);
      toast.success("Project reindex queued");
    },
  });

  const queryMutation = useMutation({
    mutationFn: (question: string) => askProject(projectId, { query: question, language: "en" }),
    onSuccess: setChatResult,
  });

  if (projectQuery.isLoading || statsQuery.isLoading || documentsQuery.isLoading || botsQuery.isLoading) {
    return <LoadingState label="Loading knowledge base..." />;
  }

  if (projectQuery.isError || statsQuery.isError || documentsQuery.isError || botsQuery.isError) {
    return <ErrorState description="Failed to load knowledge base details." />;
  }

  const project = projectQuery.data!;
  const linkedBots = (botsQuery.data || []).filter((bot) => bot.project_id === Number(projectId));
  const stats = statsQuery.data?.stats || {};
  const numberStat = (key: string) => Number(stats[key] || 0);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Knowledge base"
        title={project.name}
        description={project.description || "No description provided."}
        actions={<StatusBadge status={taskState?.status} />}
      />
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="test-chat">Test Chat</TabsTrigger>
          <TabsTrigger value="linked-bots">Linked Bots</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard title="Documents" value={formatNumber(numberStat("asset_count"))} icon={<FileText className="size-4" />} tone="info" />
            <MetricCard title="Chunks" value={formatNumber(numberStat("chunk_count"))} icon={<Boxes className="size-4" />} tone="default" />
            <MetricCard title="Total Size" value={formatBytes(numberStat("total_size"))} icon={<Database className="size-4" />} tone="success" />
            <MetricCard title="Failed Assets" value={formatNumber(numberStat("failed_assets"))} icon={<UploadCloud className="size-4" />} tone={numberStat("failed_assets") > 0 ? "danger" : "success"} />
          </div>
          <Card className="border-border/80 bg-card shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">Processing State</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-3">
              {[
                ["completed_assets", "Completed"],
                ["processing_assets", "Processing"],
                ["failed_assets", "Failed"],
              ].map(([key, label]) => (
                <div key={key} className="rounded-lg border bg-background p-3">
                  <p className="text-xs text-muted-foreground">{label}</p>
                  <p className="mt-1 text-2xl font-semibold">{formatNumber(numberStat(key))}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documents" className="space-y-4">
          <UploadDocumentCard isUploading={uploadMutation.isPending} onSelect={(file) => uploadMutation.mutate(file)} />
          <DocumentsTable
            documents={documentsQuery.data || []}
            renderActions={(document) => (
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => actionMutation.mutate({ type: "process", document })}>
                  Process
                </Button>
                <Button size="sm" onClick={() => actionMutation.mutate({ type: "processAndIndex", document })}>
                  Process + Index
                </Button>
                <ConfirmDialog
                  trigger={<Button size="sm" variant="destructive">Delete</Button>}
                  title="Delete document"
                  description="This removes the uploaded asset from the backend."
                  variant="destructive"
                  onConfirm={() => actionMutation.mutate({ type: "delete", document })}
                />
              </div>
            )}
          />
        </TabsContent>

        <TabsContent value="test-chat">
          <TestChatPanel onSubmit={(question) => queryMutation.mutate(question)} isPending={queryMutation.isPending} result={chatResult} />
        </TabsContent>

        <TabsContent value="linked-bots">
          <LinkedBotsPanel bots={linkedBots} />
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card className="border-border/80 bg-card shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">Project settings</CardTitle>
            </CardHeader>
            <CardContent>
            <p className="text-sm text-muted-foreground">
              Mutations remain backend-owned. Reindexing uses the existing task queue.
            </p>
            <Button className="mt-4" onClick={() => reindexMutation.mutate()}>
              <RefreshCw className="size-4" />
              Reindex knowledge base
            </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
