import Link from "next/link";

import { Conversation } from "@/lib/types/conversation";
import { formatRelativeDate } from "@/lib/utils/dates";

import { DataTable } from "@/components/shared/DataTable";
import { EmptyState } from "@/components/shared/EmptyState";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

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
    <Card className="shadow-sm">
      <CardHeader className="flex flex-row items-start justify-between gap-3">
        <div>
          <CardTitle>Recent conversations</CardTitle>
          <CardDescription>Latest customer conversations from the backend.</CardDescription>
        </div>
        <Link href="/conversations" className="text-sm font-medium text-primary">
          View all
        </Link>
      </CardHeader>
      <CardContent>
        <DataTable
          columns={["Customer", "Last activity", "Status"]}
          rows={conversations.slice(0, 5).map((conversation) => [
            <Link
              key={`customer-${conversation.id}`}
              href={`/conversations/${conversation.id}`}
              className="font-medium text-foreground hover:text-primary"
            >
              {conversation.customer_label}
            </Link>,
            formatRelativeDate(conversation.last_message_at),
            <StatusBadge key={`status-${conversation.id}`} status={conversation.needs_human ? "needs human" : conversation.status} />,
          ])}
        />
      </CardContent>
    </Card>
  );
}
