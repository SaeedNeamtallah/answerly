"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { MessageCircle, MessageSquareWarning, UsersRound, MessagesSquare, ArrowUpRight } from "lucide-react";

import { listConversations } from "@/lib/api/conversations";
import { queryKeys } from "@/lib/api/queryKeys";
import { formatNumber } from "@/lib/utils/formatters";

import { ConversationFilters } from "@/components/conversations/ConversationFilters";
import { ConversationList } from "@/components/conversations/ConversationList";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { Button } from "@/components/ui/button";

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
    <div className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Inbox</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage customer conversations and escalate to human agents when needed.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="h-10 rounded-xl px-4 border-slate-200 text-slate-600 bg-white">
            <ArrowUpRight className="size-4 mr-2" />
            Export Data
          </Button>
          <Button className="h-10 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm px-4">
            <MessagesSquare className="mr-2 size-4" />
            Start New Chat
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 size-24 rounded-full bg-blue-50 transition-transform group-hover:scale-150 duration-500 ease-out" />
          <div className="relative z-10">
            <div className="flex items-center gap-3 text-slate-500 mb-3">
              <div className="rounded-lg bg-blue-100 p-2 text-blue-600">
                <MessageCircle className="size-4" />
              </div>
              <h3 className="text-sm font-medium">Total Conversations</h3>
            </div>
            <div className="text-3xl font-bold text-slate-900">{formatNumber(conversations.length)}</div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 size-24 rounded-full bg-emerald-50 transition-transform group-hover:scale-150 duration-500 ease-out" />
          <div className="relative z-10">
            <div className="flex items-center gap-3 text-slate-500 mb-3">
              <div className="rounded-lg bg-emerald-100 p-2 text-emerald-600">
                <UsersRound className="size-4" />
              </div>
              <h3 className="text-sm font-medium">Open Tickets</h3>
            </div>
            <div className="text-3xl font-bold text-slate-900">{formatNumber(open)}</div>
          </div>
        </div>

        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 shadow-sm relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 size-24 rounded-full bg-rose-100 transition-transform group-hover:scale-150 duration-500 ease-out" />
          <div className="relative z-10">
            <div className="flex items-center gap-3 text-rose-600 mb-3">
              <div className="rounded-lg bg-rose-200 p-2 text-rose-700">
                <MessageSquareWarning className="size-4" />
              </div>
              <h3 className="text-sm font-medium">Needs Human</h3>
            </div>
            <div className="text-3xl font-bold text-rose-900">{formatNumber(needsHuman)}</div>
            <div className="mt-2 flex items-center gap-2 text-xs text-rose-600/80">
              <span className="text-rose-600 font-medium font-semibold">Requires immediate attention</span>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <ConversationFilters status={status} onStatusChange={setStatus} />
        <ConversationList conversations={conversations} />
      </div>
    </div>
  );
}
