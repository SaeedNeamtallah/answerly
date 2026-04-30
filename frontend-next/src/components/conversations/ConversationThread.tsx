import { ConversationMessage } from "@/lib/types/conversation";

import { EmptyState } from "@/components/shared/EmptyState";
import { MessageBubble } from "@/components/conversations/MessageBubble";

export function ConversationThread({ messages }: { messages: ConversationMessage[] }) {
  if (messages.length === 0) {
    return <EmptyState title="No messages" description="This conversation does not have messages yet." />;
  }

  return (
    <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
      {messages.map((message) => (
        <div key={message.id} className="flex">
          <MessageBubble message={message} />
        </div>
      ))}
    </div>
  );
}
