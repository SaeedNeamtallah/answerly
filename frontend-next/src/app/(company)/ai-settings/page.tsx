"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { getProviders, updateProviders } from "@/lib/api/config";
import { canAccessAdmin } from "@/lib/auth/permissions";
import { useAuthStore } from "@/store/auth-store";

import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { FormSection } from "@/components/shared/FormSection";
import { LoadingState } from "@/components/shared/LoadingState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const schema = z.object({
  llm_provider: z.string().min(1),
  embedding_provider: z.string().min(1),
  vector_db_provider: z.string().optional(),
  retrieval_top_k: z.coerce.number().min(1).max(100),
});

type FormInput = z.input<typeof schema>;
type FormValues = z.output<typeof schema>;

export default function AiSettingsPage() {
  const user = useAuthStore((state) => state.currentUser);
  const query = useQuery({
    queryKey: ["providers"],
    queryFn: getProviders,
  });
  const form = useForm<FormInput, unknown, FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      llm_provider: "",
      embedding_provider: "",
      vector_db_provider: "",
      retrieval_top_k: 5,
    },
  });

  useEffect(() => {
    if (!query.data) {
      return;
    }
    form.reset({
      llm_provider: query.data.llm_provider || "",
      embedding_provider: query.data.embedding_provider || "",
      vector_db_provider: query.data.vector_db_provider || "",
      retrieval_top_k: query.data.retrieval_top_k || 5,
    });
  }, [form, query.data]);

  const mutation = useMutation({
    mutationFn: updateProviders,
    onSuccess: () => toast.success("Provider settings saved"),
  });
  const llmProvider = useWatch({ control: form.control, name: "llm_provider" });
  const embeddingProvider = useWatch({ control: form.control, name: "embedding_provider" });
  const vectorDbProvider = useWatch({ control: form.control, name: "vector_db_provider" });

  if (!canAccessAdmin(user)) {
    return (
      <EmptyState
        title="Admin-only settings"
        description="Global provider settings are protected for platform owners until the backend becomes tenant-scoped."
      />
    );
  }

  if (query.isLoading) {
    return <LoadingState label="Loading AI settings..." />;
  }

  if (query.isError) {
    return <ErrorState description="Failed to load provider configuration." />;
  }

  const available = query.data?.available || {};

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Admin-only" title="AI Settings" description="Uses the authenticated `/config/providers` runtime config endpoints." />
      <FormSection title="Provider selections">
        <form
          className="grid gap-4 md:grid-cols-2"
          onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
        >
          <div className="space-y-2">
            <label className="text-sm font-medium">LLM provider</label>
            <Select value={llmProvider} onValueChange={(value) => form.setValue("llm_provider", value)}>
              <SelectTrigger><SelectValue placeholder="Choose provider" /></SelectTrigger>
              <SelectContent>
                {(available.llm || []).map((item) => (
                  <SelectItem key={item} value={item}>{item}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Embedding provider</label>
            <Select value={embeddingProvider} onValueChange={(value) => form.setValue("embedding_provider", value)}>
              <SelectTrigger><SelectValue placeholder="Choose provider" /></SelectTrigger>
              <SelectContent>
                {(available.embedding || []).map((item) => (
                  <SelectItem key={item} value={item}>{item}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Vector DB provider</label>
            <Select value={vectorDbProvider || ""} onValueChange={(value) => form.setValue("vector_db_provider", value)}>
              <SelectTrigger><SelectValue placeholder="Choose provider" /></SelectTrigger>
              <SelectContent>
                {(available.vector_db || []).map((item) => (
                  <SelectItem key={item} value={item}>{item}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Retrieval top K</label>
            <Input type="number" {...form.register("retrieval_top_k")} />
          </div>
          <Button type="submit" className="md:col-span-2">Save settings</Button>
        </form>
      </FormSection>
    </div>
  );
}
