"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { listConversations } from "@/lib/api/conversations";

import { PageHeader } from "@/components/layout/PageHeader";
import { ConversationFilters } from "@/components/conversations/ConversationFilters";
import { ConversationList } from "@/components/conversations/ConversationList";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function ConversationsPage() {
  const [status, setStatus] = useState("all");
  const query = useQuery({
    queryKey: ["conversations"],
    queryFn: () => listConversations(status === "all" ? undefined : { status }),
  });

  if (query.isLoading) {
    return <LoadingState label="Loading conversations..." />;
  }

  if (query.isError) {
    return <ErrorState description="Failed to load conversations." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Inbox" title="Conversations" description="Company users manage customer conversations here." />
      <ConversationFilters status={status} onStatusChange={setStatus} />
      <ConversationList conversations={query.data || []} />
    </div>
  );
}
