"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { MessageCircle, MessageSquareWarning, UsersRound } from "lucide-react";

import { listConversations } from "@/lib/api/conversations";
import { queryKeys } from "@/lib/api/queryKeys";
import { formatNumber } from "@/lib/utils/formatters";

import { PageHeader } from "@/components/layout/PageHeader";
import { ConversationFilters } from "@/components/conversations/ConversationFilters";
import { ConversationList } from "@/components/conversations/ConversationList";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { MetricCard } from "@/components/shared/MetricCard";

export default function ConversationsPage() {
  const [status, setStatus] = useState("all");
  const query = useQuery({
    queryKey: queryKeys.conversations.filtered(status),
    queryFn: () => listConversations(status === "all" ? undefined : { status }),
  });

  if (query.isLoading) {
    return <LoadingState label="Loading conversations..." />;
  }

  if (query.isError) {
    return <ErrorState description="Failed to load conversations." />;
  }

  const conversations = query.data || [];
  const needsHuman = conversations.filter((conversation) => conversation.needs_human).length;
  const open = conversations.filter((conversation) => conversation.status === "open").length;

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Inbox" title="Conversations" description="Company users manage customer conversations here." />
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard title="Loaded Conversations" value={formatNumber(conversations.length)} icon={<MessageCircle className="size-4" />} tone="info" />
        <MetricCard title="Open" value={formatNumber(open)} icon={<UsersRound className="size-4" />} tone="default" />
        <MetricCard title="Needs Human" value={formatNumber(needsHuman)} icon={<MessageSquareWarning className="size-4" />} tone={needsHuman > 0 ? "warning" : "success"} />
      </div>
      <ConversationFilters status={status} onStatusChange={setStatus} />
      <ConversationList conversations={conversations} />
    </div>
  );
}
