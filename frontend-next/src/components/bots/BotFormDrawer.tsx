"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Plus } from "lucide-react";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";

import { Project } from "@/lib/types/project";
import { BotIntegration } from "@/lib/types/bot";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  project_id: z.number().min(1, "Project is required"),
  bot_token: z.string().optional(),
  fallback_message: z.string().optional(),
  show_sources_to_customer: z.boolean().default(false),
  human_handoff_enabled: z.boolean().default(true),
});

type BotFormInput = z.input<typeof schema>;
export type BotFormValues = z.output<typeof schema>;

export function BotFormDrawer({
  projects,
  isPending,
  onSubmit,
  initialValues,
  triggerLabel = "Create bot",
}: {
  projects: Project[];
  isPending: boolean;
  onSubmit: (values: BotFormValues) => void;
  initialValues?: BotIntegration | null;
  triggerLabel?: string;
}) {
  const form = useForm<BotFormInput, unknown, BotFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initialValues?.name || "",
      project_id: initialValues?.project_id || 0,
      bot_token: "",
      fallback_message: initialValues?.fallback_message || "",
      show_sources_to_customer: initialValues?.show_sources_to_customer || false,
      human_handoff_enabled: initialValues?.human_handoff_enabled ?? true,
    },
  });

  useEffect(() => {
    if (!initialValues) {
      return;
    }

    form.reset({
      name: initialValues.name,
      project_id: initialValues.project_id,
      bot_token: "",
      fallback_message: initialValues.fallback_message || "",
      show_sources_to_customer: initialValues.show_sources_to_customer || false,
      human_handoff_enabled: initialValues.human_handoff_enabled ?? true,
    });
  }, [form, initialValues]);
  const projectId = useWatch({ control: form.control, name: "project_id" });

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button>
          <Plus className="size-4" />
          {triggerLabel}
        </Button>
      </SheetTrigger>
      <SheetContent className="w-full sm:max-w-xl">
        <SheetHeader>
          <SheetTitle>{initialValues ? "Edit bot" : "Create bot"}</SheetTitle>
        </SheetHeader>
        <form className="mt-6 space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
          <div className="space-y-2">
            <label className="text-sm font-medium">Bot name</label>
            <Input {...form.register("name")} />
          </div>
          {!initialValues ? (
            <div className="space-y-2">
              <label className="text-sm font-medium">BotFather token</label>
              <Input type="password" {...form.register("bot_token")} />
            </div>
          ) : null}
          <div className="space-y-2">
            <label className="text-sm font-medium">Linked knowledge base</label>
            <Select
              value={String(projectId || "")}
              onValueChange={(value) => form.setValue("project_id", Number(value))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select project" />
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
          <div className="space-y-2">
            <label className="text-sm font-medium">Fallback message</label>
            <Textarea rows={4} {...form.register("fallback_message")} />
          </div>
          <Button type="submit" disabled={isPending}>
            {isPending ? <Loader2 className="size-4 animate-spin" /> : null}
            Save bot
          </Button>
        </form>
      </SheetContent>
    </Sheet>
  );
}
