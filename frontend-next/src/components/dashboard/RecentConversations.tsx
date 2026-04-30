import Link from "next/link";

import { Conversation } from "@/lib/types/conversation";

import { EmptyState } from "@/components/shared/EmptyState";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatRelativeDate } from "@/lib/utils/dates";

export function RecentConversations({ conversations }: { conversations: Conversation[] }) {
  if (conversations.length === 0) {
    return (
      <EmptyState
        title="No conversations yet"
        description="Customer chats will appear here once your Telegram bot starts receiving messages."
      />
    );
  }

  return (
    <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-950">Recent conversations</h3>
        <Link href="/conversations" className="text-sm font-medium text-indigo-600">
          View all
        </Link>
      </div>
      {conversations.slice(0, 5).map((conversation) => (
        <Link
          key={conversation.id}
          href={`/conversations/${conversation.id}`}
          className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-3 transition hover:border-indigo-200 hover:bg-slate-50"
        >
          <div>
            <p className="font-medium text-slate-900">{conversation.customer_label}</p>
            <p className="text-sm text-slate-500">{formatRelativeDate(conversation.last_message_at)}</p>
          </div>
          <StatusBadge status={conversation.status} />
        </Link>
      ))}
    </div>
  );
}
