"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Loader2, Settings2, Save } from "lucide-react";

import { getApiErrorMessage } from "@/lib/api/client";
import { getProviders, updateProviders } from "@/lib/api/config";
import { queryKeys } from "@/lib/api/queryKeys";
import type { ProviderConfigResponse, ProviderConfigUpdatePayload } from "@/lib/types/config";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingState } from "@/components/shared/LoadingState";
import { ErrorState } from "@/components/shared/ErrorState";

const DEFAULT_FORM_DATA: ProviderConfigUpdatePayload = {
  llm_provider: "",
  embedding_provider: "",
  vector_db_provider: "",
  retrieval_top_k: 5,
  chunk_size: 1000,
  chunk_overlap: 200,
  retrieval_hybrid_enabled: false,
  query_rewrite_enabled: false,
};

function toFormData(config: ProviderConfigResponse | undefined): ProviderConfigUpdatePayload {
  return {
    ...DEFAULT_FORM_DATA,
    llm_provider: config?.llm_provider || "",
    embedding_provider: config?.embedding_provider || "",
    vector_db_provider: config?.vector_db_provider || "",
    retrieval_top_k: config?.retrieval_top_k || DEFAULT_FORM_DATA.retrieval_top_k,
    chunk_size: config?.chunk_size || DEFAULT_FORM_DATA.chunk_size,
    chunk_overlap: config?.chunk_overlap || DEFAULT_FORM_DATA.chunk_overlap,
    retrieval_hybrid_enabled: config?.retrieval_hybrid_enabled || false,
    query_rewrite_enabled: config?.query_rewrite_enabled || false,
  };
}

export default function PlatformSettingsPage() {
  const query = useQuery({
    queryKey: queryKeys.providers,
    queryFn: getProviders,
  });

  if (query.isLoading) return <LoadingState label="Loading platform settings..." />;
  if (query.isError) return <ErrorState description="Failed to load settings." />;

  const initialFormData = toFormData(query.data);
  const formKey = JSON.stringify(initialFormData);

  return (
    <PlatformSettingsForm
      key={formKey}
      available={query.data?.available || {}}
      initialFormData={initialFormData}
    />
  );
}

function PlatformSettingsForm({
  available,
  initialFormData,
}: {
  available: NonNullable<ProviderConfigResponse["available"]>;
  initialFormData: ProviderConfigUpdatePayload;
}) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<ProviderConfigUpdatePayload>(initialFormData);
  const mutation = useMutation({
    mutationFn: updateProviders,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.providers });
      toast.success("Platform settings updated successfully");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to update platform settings"));
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <div className="space-y-8 pb-10 max-w-4xl">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Platform Settings</h1>
        <p className="text-sm text-slate-500 mt-1">
          Manage global AI providers, vector database, and retrieval configurations.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings2 className="size-5 text-indigo-600" />
              AI Providers
            </CardTitle>
            <CardDescription>Select the core AI models and services used across the platform.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="llm_provider">LLM Provider</Label>
              <select
                id="llm_provider"
                className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={formData.llm_provider}
                onChange={(e) => setFormData({ ...formData, llm_provider: e.target.value })}
              >
                {available.llm?.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="embedding_provider">Embedding Provider</Label>
              <select
                id="embedding_provider"
                className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={formData.embedding_provider}
                onChange={(e) => setFormData({ ...formData, embedding_provider: e.target.value })}
              >
                {available.embedding?.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="vector_db_provider">Vector DB Provider</Label>
              <select
                id="vector_db_provider"
                className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={formData.vector_db_provider}
                onChange={(e) => setFormData({ ...formData, vector_db_provider: e.target.value })}
              >
                {available.vector_db?.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Retrieval & Chunking</CardTitle>
            <CardDescription>Configure how documents are processed and retrieved.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="chunk_size">Chunk Size</Label>
                <Input
                  id="chunk_size"
                  type="number"
                  value={formData.chunk_size || 1000}
                  onChange={(e) => setFormData({ ...formData, chunk_size: parseInt(e.target.value) })}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="chunk_overlap">Chunk Overlap</Label>
                <Input
                  id="chunk_overlap"
                  type="number"
                  value={formData.chunk_overlap || 200}
                  onChange={(e) => setFormData({ ...formData, chunk_overlap: parseInt(e.target.value) })}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="retrieval_top_k">Retrieval Top K</Label>
                <Input
                  id="retrieval_top_k"
                  type="number"
                  value={formData.retrieval_top_k || 5}
                  onChange={(e) => setFormData({ ...formData, retrieval_top_k: parseInt(e.target.value) })}
                />
              </div>
            </div>

            <div className="flex items-center justify-between mt-4">
              <div>
                <Label>Hybrid Retrieval</Label>
                <p className="text-xs text-slate-500">Enable keyword + semantic search.</p>
              </div>
              <Switch
                checked={formData.retrieval_hybrid_enabled}
                onCheckedChange={(c) => setFormData({ ...formData, retrieval_hybrid_enabled: c })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label>Query Rewrite</Label>
                <p className="text-xs text-slate-500">Use LLM to rewrite user queries for better retrieval.</p>
              </div>
              <Switch
                checked={formData.query_rewrite_enabled}
                onCheckedChange={(c) => setFormData({ ...formData, query_rewrite_enabled: c })}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" disabled={mutation.isPending} className="bg-indigo-600 hover:bg-indigo-700">
            {mutation.isPending ? <Loader2 className="mr-2 size-4 animate-spin" /> : <Save className="mr-2 size-4" />}
            Save Settings
          </Button>
        </div>
      </form>
    </div>
  );
}
