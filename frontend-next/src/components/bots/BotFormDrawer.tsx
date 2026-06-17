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
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  project_id: z.number().min(1, "Project is required"),
  bot_token: z.string().optional(),
  fallback_message: z
    .string()
    .optional()
    .transform((value) => {
      const trimmed = String(value || "").trim();
      return trimmed ? trimmed : null;
    }),
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
  trigger,
}: {
  projects: Project[];
  isPending: boolean;
  onSubmit: (values: BotFormValues) => void;
  initialValues?: BotIntegration | null;
  triggerLabel?: string;
  trigger?: React.ReactNode;
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
  const showSourcesToCustomer = useWatch({ control: form.control, name: "show_sources_to_customer" });
  const humanHandoffEnabled = useWatch({ control: form.control, name: "human_handoff_enabled" });

  return (
    <Sheet>
      <SheetTrigger asChild>
        {trigger || (
          <Button>
            <Plus data-icon="inline-start" />
            {triggerLabel}
          </Button>
        )}
      </SheetTrigger>
      <SheetContent className="w-full sm:max-w-xl">
        <SheetHeader>
          <SheetTitle>{initialValues ? "Edit bot" : "Create bot"}</SheetTitle>
          <SheetDescription>
            Values are submitted to the existing bot integration backend endpoints. Saved Telegram tokens are not displayed.
          </SheetDescription>
        </SheetHeader>
        <form className="mt-6 flex flex-col gap-4" onSubmit={form.handleSubmit(onSubmit)}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="bot-name">Bot name</Label>
            <Input id="bot-name" {...form.register("name")} />
          </div>
          {!initialValues ? (
            <div className="flex flex-col gap-2">
              <Label htmlFor="bot-token">BotFather token</Label>
              <Input id="bot-token" type="password" {...form.register("bot_token")} />
            </div>
          ) : null}
          <div className="flex flex-col gap-2">
            <Label>Linked knowledge base</Label>
            <Select
              value={String(projectId || "")}
              onValueChange={(value) => form.setValue("project_id", Number(value))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select project" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {projects.map((project) => (
                    <SelectItem key={project.id} value={String(project.id)}>
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="bot-fallback-message">Fallback message</Label>
            <Textarea id="bot-fallback-message" rows={4} {...form.register("fallback_message")} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="flex min-h-24 items-start justify-between gap-3 rounded-lg border bg-background p-3">
              <span className="flex flex-col gap-1">
                <span className="text-sm font-medium">Customer sources</span>
                <span className="text-sm text-muted-foreground">Show source context in Telegram replies.</span>
              </span>
              <Switch
                checked={Boolean(showSourcesToCustomer)}
                onCheckedChange={(checked) => form.setValue("show_sources_to_customer", checked, { shouldDirty: true })}
              />
            </label>
            <label className="flex min-h-24 items-start justify-between gap-3 rounded-lg border bg-background p-3">
              <span className="flex flex-col gap-1">
                <span className="text-sm font-medium">Human handoff</span>
                <span className="text-sm text-muted-foreground">Allow conversations to be escalated.</span>
              </span>
              <Switch
                checked={Boolean(humanHandoffEnabled)}
                onCheckedChange={(checked) => form.setValue("human_handoff_enabled", checked, { shouldDirty: true })}
              />
            </label>
          </div>
          <Button type="submit" disabled={isPending}>
            {isPending ? <Loader2 data-icon="inline-start" className="animate-spin" /> : null}
            Save bot
          </Button>
        </form>
      </SheetContent>
    </Sheet>
  );
}
