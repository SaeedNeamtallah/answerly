import { Conversation } from "@/lib/types/conversation";

import { formatDateTime } from "@/lib/utils/dates";
import { Info, User, Bot, AlertCircle, Clock, Hash, ShieldAlert, MessageCircle } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export function ConversationMetadataPanel({ conversation }: { conversation?: Conversation | null }) {
  if (!conversation) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-6 text-sm text-slate-500 shadow-sm text-center">
        <Info className="size-6 text-slate-400 mx-auto mb-2" />
        Select a conversation to inspect metadata.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="border-b border-slate-200 bg-slate-50/50 px-5 py-4 flex items-center justify-between">
        <h3 className="font-semibold text-slate-900 flex items-center gap-2">
          <Info className="size-4 text-indigo-500" />
          Details
        </h3>
        <span className={cn(
          "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ring-1 ring-inset capitalize",
          conversation.status === "open" ? "bg-indigo-50 text-indigo-700 ring-indigo-200" :
          conversation.status === "resolved" ? "bg-emerald-50 text-emerald-700 ring-emerald-200" :
          conversation.status === "escalated" ? "bg-amber-50 text-amber-700 ring-amber-200" :
          "bg-slate-50 text-slate-700 ring-slate-200"
        )}>
          {conversation.status}
        </span>
      </div>
      <div className="p-5 space-y-4 text-sm">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-lg bg-indigo-50 p-1.5 text-indigo-600">
            <User className="size-4" />
          </div>
          <div>
            <p className="font-medium text-slate-900">{conversation.customer_label}</p>
            <p className="text-xs text-slate-500 mt-0.5">Customer Name</p>
          </div>
        </div>
        
        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-lg bg-blue-50 p-1.5 text-blue-600">
            <Bot className="size-4" />
          </div>
          <div>
            <p className="font-medium text-slate-900">{conversation.bot_name || `Bot #${conversation.bot_integration_id || conversation.whatsapp_integration_id}`}</p>
            <p className="text-xs text-slate-500 mt-0.5">Assigned Bot</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-lg bg-indigo-50 p-1.5 text-indigo-600">
            <MessageCircle className="size-4" />
          </div>
          <div>
            <p className="font-medium text-slate-900 capitalize">{conversation.channel === 'whatsapp' ? 'WhatsApp' : 'Telegram'}</p>
            <p className="text-xs text-slate-500 mt-0.5">Channel</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-lg bg-slate-100 p-1.5 text-slate-600">
            <Hash className="size-4" />
          </div>
          <div>
            <p className="font-medium text-slate-900">{conversation.project_id}</p>
            <p className="text-xs text-slate-500 mt-0.5">Project ID</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className={cn("mt-0.5 rounded-lg p-1.5", conversation.needs_human ? "bg-rose-50 text-rose-600" : "bg-emerald-50 text-emerald-600")}>
            {conversation.needs_human ? <AlertCircle className="size-4" /> : <ShieldAlert className="size-4" />}
          </div>
          <div>
            <p className="font-medium text-slate-900">{conversation.needs_human ? "Yes" : "No"}</p>
            <p className="text-xs text-slate-500 mt-0.5">Needs Human Agent</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-lg bg-amber-50 p-1.5 text-amber-600">
            <Clock className="size-4" />
          </div>
          <div>
            <p className="font-medium text-slate-900">{formatDateTime(conversation.last_message_at)}</p>
            <p className="text-xs text-slate-500 mt-0.5">Last Message</p>
          </div>
        </div>
      </div>
    </div>
  );
}
