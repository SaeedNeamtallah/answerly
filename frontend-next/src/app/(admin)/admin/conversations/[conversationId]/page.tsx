"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { getAdminConversation, getAdminConversationMessages } from "@/lib/api/admin";
import { queryKeys } from "@/lib/api/queryKeys";

import { PageHeader } from "@/components/layout/PageHeader";
import { ConversationThread } from "@/components/conversations/ConversationThread";
import { SourceMetadataPanel } from "@/components/conversations/SourceMetadataPanel";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function AdminConversationDetailPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const conversationQuery = useQuery({
    queryKey: queryKeys.admin.conversation(conversationId),
    queryFn: () => getAdminConversation(conversationId),
  });
  const messagesQuery = useQuery({
    queryKey: queryKeys.admin.conversationMessages(conversationId),
    queryFn: () => getAdminConversationMessages(conversationId),
  });

  if (conversationQuery.isLoading || messagesQuery.isLoading) {
    return <LoadingState label="Loading admin conversation..." />;
  }

  if (conversationQuery.isError || messagesQuery.isError) {
    return <ErrorState description="Failed to load admin conversation detail." />;
  }

  const lastMessageWithSources = [...(messagesQuery.data || [])]
    .reverse()
    .find((message) => message.answer_sources_json?.length || message.retrieval_metadata_json);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Read-only detail"
        title={`Conversation #${conversationQuery.data!.id}`}
        description="Platform-owner read-only thread and internal retrieval inspection."
      />
      <ConversationThread
        messages={(messagesQuery.data || []).map((message) => ({
          id: message.id,
          conversation_id: message.conversation_id,
          sender_type: message.sender_type,
          text: message.text,
          agent_user_id: null,
          telegram_message_id: null,
          answer_sources_json: message.answer_sources_json,
          retrieval_metadata_json: message.retrieval_metadata_json,
          created_at: message.created_at,
        }))}
      />
      <SourceMetadataPanel
        message={
          lastMessageWithSources
            ? {
                id: lastMessageWithSources.id,
                conversation_id: lastMessageWithSources.conversation_id,
                sender_type: lastMessageWithSources.sender_type,
                text: lastMessageWithSources.text,
                answer_sources_json: lastMessageWithSources.answer_sources_json,
                retrieval_metadata_json: lastMessageWithSources.retrieval_metadata_json,
                created_at: lastMessageWithSources.created_at,
              }
            : null
        }
      />
    </div>
  );
}
