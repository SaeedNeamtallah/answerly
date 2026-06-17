"use client";

import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { CheckCircle2, Hand, ShieldAlert, UserRoundCheck, ArrowLeft, MoreHorizontal, MessageSquareText, Hash } from "lucide-react";

import {
  assignConversation,
  blockCustomer,
  escalateConversation,
  getConversation,
  getConversationMessages,
  replyToConversation,
  resolveConversation,
} from "@/lib/api/conversations";

import { ConversationMetadataPanel } from "@/components/conversations/ConversationMetadataPanel";
import { ConversationThread } from "@/components/conversations/ConversationThread";
import { ReplyComposer } from "@/components/conversations/ReplyComposer";
import { SourceMetadataPanel } from "@/components/conversations/SourceMetadataPanel";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";

export default function ConversationDetailPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const router = useRouter();
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

  const conversation = conversationQuery.data!;

  return (
    <div className="space-y-6 pb-10">
      <div className="flex items-center gap-4 border-b border-slate-200 pb-4">
        <button 
          onClick={() => router.push("/conversations")}
          className="flex size-10 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-sm transition-colors hover:bg-slate-50 hover:text-slate-900"
        >
          <ArrowLeft className="size-4" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <h1 className="truncate text-2xl font-bold text-slate-900 tracking-tight">
              {conversation.customer_label}
            </h1>
            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium ring-1 ring-inset capitalize bg-indigo-50 text-indigo-700 ring-indigo-200">
              {conversation.status}
            </span>
            {conversation.needs_human && (
              <span className="inline-flex items-center gap-1 rounded-md bg-rose-50 px-2 py-1 text-xs font-medium text-rose-600 ring-1 ring-inset ring-rose-200">
                <UserRoundCheck className="size-3.5" />
                Human requested
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 mt-1 flex items-center gap-2">
            <Hash className="size-4 text-slate-400" />
            Conversation #{conversation.id} • Assigned to: {conversation.assigned_to_user_id ? "You" : "Unassigned"}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
            <Button variant="ghost" size="sm" onClick={() => statusMutation.mutate("assign")} className="h-8 text-slate-600 hover:text-indigo-600 hover:bg-indigo-50">
              <UserRoundCheck className="mr-2 size-4" /> Assign
            </Button>
            <div className="w-px h-4 bg-slate-200" />
            <Button variant="ghost" size="sm" onClick={() => statusMutation.mutate("escalate")} className="h-8 text-slate-600 hover:text-amber-600 hover:bg-amber-50">
              <Hand className="mr-2 size-4" /> Escalate
            </Button>
            <div className="w-px h-4 bg-slate-200" />
            <Button variant="ghost" size="sm" onClick={() => statusMutation.mutate("resolve")} className="h-8 text-slate-600 hover:text-emerald-600 hover:bg-emerald-50">
              <CheckCircle2 className="mr-2 size-4" /> Resolve
            </Button>
            <div className="w-px h-4 bg-slate-200" />
            <Button variant="ghost" size="sm" onClick={() => statusMutation.mutate("block")} className="h-8 text-slate-600 hover:text-rose-600 hover:bg-rose-50">
              <ShieldAlert className="mr-2 size-4" /> Block
            </Button>
          </div>
          <button className="flex size-10 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 shadow-sm transition-colors hover:bg-slate-50 hover:text-slate-900">
            <MoreHorizontal className="size-4" />
          </button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr] h-[calc(100vh-200px)] min-h-[600px]">
        <div className="flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="flex-1 overflow-hidden relative">
            <div className="absolute inset-0 bg-slate-50/50" />
            <ConversationThread messages={messagesQuery.data || []} />
          </div>
          <div className="p-4 border-t border-slate-200 bg-white">
            <ReplyComposer isPending={replyMutation.isPending} onSend={(text) => replyMutation.mutate(text)} />
          </div>
        </div>
        <div className="space-y-6 overflow-y-auto pr-2 custom-scrollbar">
          <ConversationMetadataPanel conversation={conversationQuery.data} />
          <SourceMetadataPanel message={lastMessageWithSources} />
        </div>
      </div>
    </div>
  );
}
