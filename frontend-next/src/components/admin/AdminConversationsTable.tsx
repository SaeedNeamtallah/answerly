import Link from "next/link";
import { ExternalLink } from "lucide-react";

import { AdminConversation } from "@/lib/types/admin";

import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function AdminConversationsTable({ conversations }: { conversations: AdminConversation[] }) {
  return (
    <DataTable
      caption="Cross-company conversations"
      columns={["Conversation", "Company", "Project", "Status", "Needs Human", "Open"]}
      rows={conversations.map((conversation) => [
        `#${conversation.id}`,
        String(conversation.owner_id),
        String(conversation.project_id),
        <StatusBadge key={conversation.id} status={conversation.status} />,
        <Badge key={`needs-human-${conversation.id}`} variant="outline" className="rounded-md">
          {conversation.needs_human ? "Yes" : "No"}
        </Badge>,
        <Button key={`conversation-${conversation.id}`} asChild size="sm" variant="outline">
          <Link href={`/admin/conversations/${conversation.id}`}>
            <ExternalLink className="size-3.5" />
            Inspect
          </Link>
        </Button>,
      ])}
    />
  );
}
