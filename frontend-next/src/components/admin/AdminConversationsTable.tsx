import Link from "next/link";

import { AdminConversation } from "@/lib/types/admin";

import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";

export function AdminConversationsTable({ conversations }: { conversations: AdminConversation[] }) {
  return (
    <DataTable
      columns={["Conversation", "Company", "Status", "Needs Human", "Open"]}
      rows={conversations.map((conversation) => [
        `#${conversation.id}`,
        String(conversation.owner_id),
        <StatusBadge key={conversation.id} status={conversation.status} />,
        conversation.needs_human ? "Yes" : "No",
        <Link key={`conversation-${conversation.id}`} href={`/admin/conversations/${conversation.id}`} className="text-indigo-600">
          Inspect
        </Link>,
      ])}
    />
  );
}
