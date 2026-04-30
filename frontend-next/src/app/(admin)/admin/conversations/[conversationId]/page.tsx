"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { getAdminConversation, getAdminConversationMessages } from "@/lib/api/admin";

import { PageHeader } from "@/components/layout/PageHeader";
import { ConversationThread } from "@/components/conversations/ConversationThread";
import { SourceMetadataPanel } from "@/components/conversations/SourceMetadataPanel";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function AdminConversationDetailPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const conversationQuery = useQuery({
    queryKey: ["adminConversation", conversationId],
    queryFn: () => getAdminConversation(conversationId),
  });
  const messagesQuery = useQuery({
    queryKey: ["adminConversationMessages", conversationId],
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
        description="Platform owners can inspect the full thread but cannot reply here in v1."
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
