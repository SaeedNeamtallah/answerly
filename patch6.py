with open('frontend-next/src/components/bots/BotFormDrawer.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '  show_sources_to_customer: z.boolean().default(false),\n  human_handoff_enabled: z.boolean().default(true),\n});',
    '  system_prompt: z.string().optional().transform((value) => { const trimmed = String(value || "").trim(); return trimmed ? trimmed : null; }),\n  show_sources_to_customer: z.boolean().default(false),\n  human_handoff_enabled: z.boolean().default(true),\n});'
)

text = text.replace(
    '      fallback_message: initialValues?.fallback_message || "",\n      show_sources_to_customer: initialValues?.show_sources_to_customer || false,',
    '      fallback_message: initialValues?.fallback_message || "",\n      system_prompt: initialValues?.system_prompt || "",\n      show_sources_to_customer: initialValues?.show_sources_to_customer || false,'
)

text = text.replace(
    '      fallback_message: initialValues.fallback_message || "",\n      show_sources_to_customer: initialValues.show_sources_to_customer || false,',
    '      fallback_message: initialValues.fallback_message || "",\n      system_prompt: initialValues.system_prompt || "",\n      show_sources_to_customer: initialValues.show_sources_to_customer || false,'
)

text = text.replace(
    '          <div className="flex flex-col gap-2">\n            <Label htmlFor="bot-fallback-message">Fallback message</Label>\n            <Textarea id="bot-fallback-message" rows={4} {...form.register("fallback_message")} />\n          </div>',
    '          <div className="flex flex-col gap-2">\n            <Label htmlFor="bot-system-prompt">System Prompt / Persona</Label>\n            <Textarea id="bot-system-prompt" rows={4} placeholder="e.g. You are a legal expert bot..." {...form.register("system_prompt")} />\n          </div>\n          <div className="flex flex-col gap-2">\n            <Label htmlFor="bot-fallback-message">Fallback message</Label>\n            <Textarea id="bot-fallback-message" rows={4} {...form.register("fallback_message")} />\n          </div>'
)

with open('frontend-next/src/components/bots/BotFormDrawer.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
