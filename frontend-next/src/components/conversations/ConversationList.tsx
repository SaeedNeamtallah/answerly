import Link from "next/link";
import { ChevronRight, MessageCircle, UserRoundCheck } from "lucide-react";

import { Conversation } from "@/lib/types/conversation";

import { EmptyState } from "@/components/shared/EmptyState";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatRelativeDate } from "@/lib/utils/dates";
import { Badge } from "@/components/ui/badge";

export function ConversationList({ conversations }: { conversations: Conversation[] }) {
  if (conversations.length === 0) {
    return <EmptyState title="No conversations" description="Customer conversations will appear here." />;
  }

  return (
    <div className="grid gap-3">
      {conversations.map((conversation) => (
        <Link
          key={conversation.id}
          href={`/conversations/${conversation.id}`}
          className="group block rounded-xl border bg-card p-4 shadow-sm transition-colors hover:border-primary/30 hover:bg-primary/5"
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <MessageCircle className="size-4" />
              </span>
              <div className="min-w-0">
                <p className="truncate font-medium text-foreground">{conversation.customer_label}</p>
                <p className="truncate text-sm text-muted-foreground">
                  {conversation.bot_name || `Bot #${conversation.bot_integration_id}`} · {formatRelativeDate(conversation.last_message_at)}
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {conversation.needs_human ? (
                <Badge variant="outline" className="hidden rounded-md border-amber-200 bg-amber-50 text-amber-700 sm:inline-flex">
                  <UserRoundCheck className="size-3" />
                  Needs human
                </Badge>
              ) : null}
              <StatusBadge status={conversation.status} />
              <ChevronRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
