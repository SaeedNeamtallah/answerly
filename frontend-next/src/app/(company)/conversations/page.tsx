"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { listConversations } from "@/lib/api/conversations";
import { useAuthStore } from "@/store/auth-store";

import { PageHeader } from "@/components/layout/PageHeader";
import { ConversationFilters } from "@/components/conversations/ConversationFilters";
import { ConversationList } from "@/components/conversations/ConversationList";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function ConversationsPage() {
  const [status, setStatus] = useState("all");
  const currentUser = useAuthStore((state) => state.currentUser);
  const query = useQuery({
    queryKey: ["conversations", status],
    queryFn: () => listConversations(status === "all" ? undefined : { status }),
  });

  if (query.isLoading) {
    return <LoadingState label="Loading conversations..." />;
  }

  if (query.isError) {
    return <ErrorState description="Failed to load conversations." />;
  }

  const description = currentUser?.role === "employee"
    ? `Employee ${currentUser.username} managing conversations for ${currentUser.company_name || "the company"}.`
    : "Company users manage customer conversations here.";

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Inbox" title="Conversations" description={description} />
      <ConversationFilters status={status} onStatusChange={setStatus} />
      <ConversationList conversations={query.data || []} />
    </div>
  );
}
