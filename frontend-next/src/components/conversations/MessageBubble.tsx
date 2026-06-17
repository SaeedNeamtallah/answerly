import { ConversationMessage } from "@/lib/types/conversation";
import { formatDateTime } from "@/lib/utils/dates";
import { cn } from "@/lib/utils/cn";
import { Bot, User } from "lucide-react";

export function MessageBubble({ message }: { message: ConversationMessage }) {
  const isCustomer = message.sender_type === "customer";

  return (
    <div className={cn("flex gap-3 w-full max-w-[85%]", isCustomer ? "mr-auto" : "ml-auto flex-row-reverse")}>
      <div className={cn(
        "flex size-8 shrink-0 items-center justify-center rounded-full text-white shadow-sm mt-auto",
        isCustomer ? "bg-slate-300" : "bg-indigo-500"
      )}>
        {isCustomer ? <User className="size-4" /> : <Bot className="size-4" />}
      </div>
      <div className="flex flex-col gap-1.5 min-w-0">
        <div
          className={cn(
            "rounded-2xl px-5 py-3.5 shadow-sm text-sm leading-relaxed",
            isCustomer 
              ? "rounded-bl-none border border-slate-200 bg-white text-slate-700" 
              : "rounded-br-none bg-indigo-600 text-white"
          )}
        >
          <p className="whitespace-pre-wrap">{message.text}</p>
        </div>
        <p className={cn("text-[11px] font-medium px-1", isCustomer ? "text-slate-400 text-left" : "text-slate-400 text-right")}>
          {formatDateTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}
