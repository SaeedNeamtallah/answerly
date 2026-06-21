"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Plus } from "lucide-react";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";

import { Project } from "@/lib/types/project";
import { WhatsAppIntegration } from "@/lib/api/whatsappIntegrations";

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
  phone_number: z.string().optional().transform((v) => v || undefined),
  fallback_message: z
    .string()
    .optional()
    .transform((value) => {
      const trimmed = String(value || "").trim();
      return trimmed ? trimmed : undefined;
    }),
  system_prompt: z.string().optional().transform((value) => { const trimmed = String(value || "").trim(); return trimmed ? trimmed : undefined; }),
  show_sources_to_customer: z.boolean().default(false),
  human_handoff_enabled: z.boolean().default(true),
});

type BotFormInput = z.input<typeof schema>;
export type BotFormValues = z.output<typeof schema>;

export function WhatsAppBotFormDrawer({
  projects,
  isPending,
  onSubmit,
  initialValues,
  triggerLabel = "Create WhatsApp Bot",
  trigger,
}: {
  projects: Project[];
  isPending: boolean;
  onSubmit: (values: BotFormValues) => void;
  initialValues?: WhatsAppIntegration | null;
  triggerLabel?: string;
  trigger?: React.ReactNode;
}) {
  const form = useForm<BotFormInput, unknown, BotFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initialValues?.name || "",
      project_id: initialValues?.project_id || 0,
      phone_number: initialValues?.phone_number || "",
      fallback_message: initialValues?.fallback_message || "",
      system_prompt: initialValues?.system_prompt || "",
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
      phone_number: initialValues.phone_number || "",
      fallback_message: initialValues.fallback_message || "",
      system_prompt: initialValues.system_prompt || "",
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
      <SheetContent className="w-full sm:max-w-xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{initialValues ? "Edit WhatsApp Bot" : "Create WhatsApp Bot"}</SheetTitle>
          <SheetDescription>
            Configure your WhatsApp integration. After creation, you will scan a QR code to link your WhatsApp account.
          </SheetDescription>
        </SheetHeader>
        <form className="mt-6 flex flex-col gap-4" onSubmit={form.handleSubmit(onSubmit)}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="bot-name">Bot name</Label>
            <Input id="bot-name" {...form.register("name")} />
          </div>
          
          <div className="flex flex-col gap-2">
            <Label htmlFor="phone-number">Phone Number (Optional)</Label>
            <Input id="phone-number" placeholder="e.g. +1234567890" {...form.register("phone_number")} />
          </div>
          
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
            <Label htmlFor="bot-system-prompt">System Prompt / Persona</Label>
            <Textarea id="bot-system-prompt" rows={4} placeholder="e.g. You are a helpful WhatsApp assistant..." {...form.register("system_prompt")} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="bot-fallback-message">Fallback message</Label>
            <Textarea id="bot-fallback-message" rows={4} {...form.register("fallback_message")} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="flex min-h-24 items-start justify-between gap-3 rounded-lg border bg-background p-3">
              <span className="flex flex-col gap-1">
                <span className="text-sm font-medium">Customer sources</span>
                <span className="text-sm text-muted-foreground">Show source context in replies.</span>
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
