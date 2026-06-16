import { Conversation } from "@/lib/types/conversation";

import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatDateTime } from "@/lib/utils/dates";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ConversationMetadataPanel({ conversation }: { conversation?: Conversation | null }) {
  if (!conversation) {
    return (
      <div className="rounded-xl border bg-card p-4 text-sm text-muted-foreground shadow-sm">
        Select a conversation to inspect metadata.
      </div>
    );
  }

  return (
    <Card className="border-border/80 bg-card shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle className="text-base">Metadata</CardTitle>
        <StatusBadge status={conversation.status} />
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {[
          ["Customer", conversation.customer_label],
          ["Bot", conversation.bot_name || "—"],
          ["Project ID", conversation.project_id],
          ["Needs human", conversation.needs_human ? "Yes" : "No"],
          ["Last message", formatDateTime(conversation.last_message_at)],
          ["Last error", conversation.last_error || "—"],
        ].map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 rounded-lg border bg-background px-3 py-2">
            <span className="text-muted-foreground">{label}</span>
            <span className="max-w-[60%] truncate text-right font-medium text-foreground">{value}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
