"use client";

import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  assignConversation,
  blockCustomer,
  escalateConversation,
  getConversation,
  getConversationMessages,
  replyToConversation,
  resolveConversation,
} from "@/lib/api/conversations";

import { PageHeader } from "@/components/layout/PageHeader";
import { ConversationMetadataPanel } from "@/components/conversations/ConversationMetadataPanel";
import { ConversationThread } from "@/components/conversations/ConversationThread";
import { ReplyComposer } from "@/components/conversations/ReplyComposer";
import { SourceMetadataPanel } from "@/components/conversations/SourceMetadataPanel";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function ConversationDetailPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const queryClient = useQueryClient();

  const conversationQuery = useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => getConversation(conversationId),
  });
  const messagesQuery = useQuery({
    queryKey: ["messages", conversationId],
    queryFn: () => getConversationMessages(conversationId),
  });

  const refreshKeys = () => {
    queryClient.invalidateQueries({ queryKey: ["conversations"] });
    queryClient.invalidateQueries({ queryKey: ["conversation", conversationId] });
    queryClient.invalidateQueries({ queryKey: ["messages", conversationId] });
  };

  const replyMutation = useMutation({
    mutationFn: (text: string) => replyToConversation(conversationId, { text }),
    onSuccess: () => {
      toast.success("Reply sent");
      refreshKeys();
    },
  });
  const statusMutation = useMutation({
    mutationFn: async (action: "assign" | "resolve" | "escalate" | "block") => {
      if (action === "assign") return assignConversation(conversationId);
      if (action === "resolve") return resolveConversation(conversationId);
      if (action === "escalate") return escalateConversation(conversationId);
      return blockCustomer(conversationId);
    },
    onSuccess: () => refreshKeys(),
  });

  if (conversationQuery.isLoading || messagesQuery.isLoading) {
    return <LoadingState label="Loading conversation..." />;
  }

  if (conversationQuery.isError || messagesQuery.isError) {
    return <ErrorState description="Failed to load conversation." />;
  }

  const lastMessageWithSources = [...(messagesQuery.data || [])]
    .reverse()
    .find((message) => message.answer_sources_json?.length || message.retrieval_metadata_json);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Conversation detail"
        title={conversationQuery.data!.customer_label}
        description="Internal sources and retrieval metadata remain visible only inside the dashboard."
      />
      <div className="flex flex-wrap gap-3">
        <Button variant="outline" onClick={() => statusMutation.mutate("assign")}>Assign to me</Button>
        <Button variant="outline" onClick={() => statusMutation.mutate("escalate")}>Escalate</Button>
        <Button variant="outline" onClick={() => statusMutation.mutate("resolve")}>Resolve</Button>
        <Button variant="destructive" onClick={() => statusMutation.mutate("block")}>Block customer</Button>
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-4">
          <ReplyComposer isPending={replyMutation.isPending} onSend={(text) => replyMutation.mutate(text)} />
          <ConversationThread messages={messagesQuery.data || []} />
        </div>
        <div className="space-y-4">
          <ConversationMetadataPanel conversation={conversationQuery.data} />
          <SourceMetadataPanel message={lastMessageWithSources} />
        </div>
      </div>
    </div>
  );
}
