import { ConversationMessage } from "@/lib/types/conversation";
import { formatDateTime } from "@/lib/utils/dates";

import { cn } from "@/lib/utils/cn";

export function MessageBubble({ message }: { message: ConversationMessage }) {
  const isCustomer = message.sender_type === "customer";

  return (
    <div
      className={cn(
        "max-w-[85%] rounded-2xl px-4 py-3 shadow-sm",
        isCustomer ? "mr-auto bg-white border border-slate-200" : "ml-auto bg-indigo-600 text-white",
      )}
    >
      <p className="whitespace-pre-wrap text-sm">{message.text}</p>
      <p className={cn("mt-2 text-xs", isCustomer ? "text-slate-500" : "text-indigo-100")}>
        {message.sender_type} · {formatDateTime(message.created_at)}
      </p>
    </div>
  );
}
