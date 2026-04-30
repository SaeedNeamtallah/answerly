"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { createProject } from "@/lib/api/projects";
import { ApiError } from "@/lib/api/client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function KnowledgeBaseFormDialog() {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", description: "" },
  });

  const mutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      toast.success("Knowledge base created");
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setOpen(false);
      form.reset();
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Failed to create knowledge base");
    },
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" />
          New knowledge base
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create knowledge base</DialogTitle>
          <DialogDescription>Backend projects remain the source of truth for this entity.</DialogDescription>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={form.handleSubmit((values) => mutation.mutate({ ...values, metadata: {} }))}
        >
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <Input {...form.register("name")} />
            <p className="text-sm text-rose-600">{form.formState.errors.name?.message}</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Description</label>
            <Textarea rows={4} {...form.register("description")} />
          </div>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
            Create
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
