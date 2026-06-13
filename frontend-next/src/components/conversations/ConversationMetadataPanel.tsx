import { Conversation } from "@/lib/types/conversation";

import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatDateTime } from "@/lib/utils/dates";

export function ConversationMetadataPanel({ conversation }: { conversation?: Conversation | null }) {
  if (!conversation) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm">
        Select a conversation to inspect metadata.
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-950">Metadata</h3>
        <StatusBadge status={conversation.status} />
      </div>
      <div className="space-y-2 text-sm text-slate-600">
        <p>Customer: {conversation.customer_label}</p>
        <p>Bot: {conversation.bot_name || "—"}</p>
        <p>Project ID: {conversation.project_id}</p>
        <p>Needs human: {conversation.needs_human ? "Yes" : "No"}</p>
        <p>Assigned to: {conversation.assigned_to_username || "Unassigned"}</p>
        <p>Last message: {formatDateTime(conversation.last_message_at)}</p>
        <p>Last error: {conversation.last_error || "—"}</p>
      </div>
    </div>
  );
}
