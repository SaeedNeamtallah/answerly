import Link from "next/link";

import { Conversation } from "@/lib/types/conversation";

import { EmptyState } from "@/components/shared/EmptyState";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatRelativeDate } from "@/lib/utils/dates";

export function ConversationList({ conversations }: { conversations: Conversation[] }) {
  if (conversations.length === 0) {
    return <EmptyState title="No conversations" description="Customer conversations will appear here." />;
  }

  return (
    <div className="space-y-3">
      {conversations.map((conversation) => (
        <Link
          key={conversation.id}
          href={`/conversations/${conversation.id}`}
          className="block rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-indigo-200"
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="font-medium text-slate-900">{conversation.customer_label}</p>
              <p className="text-sm text-slate-500">{formatRelativeDate(conversation.last_message_at)}</p>
            </div>
            <StatusBadge status={conversation.status} />
          </div>
        </Link>
      ))}
    </div>
  );
}
