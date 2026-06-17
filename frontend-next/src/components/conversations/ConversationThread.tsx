import { ConversationMessage } from "@/lib/types/conversation";

import { EmptyState } from "@/components/shared/EmptyState";
import { MessageBubble } from "@/components/conversations/MessageBubble";

export function ConversationThread({ messages }: { messages: ConversationMessage[] }) {
  if (messages.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <EmptyState title="No messages" description="This conversation does not have messages yet." />
      </div>
    );
  }

  return (
    <div className="absolute inset-0 overflow-y-auto p-6 space-y-4 custom-scrollbar">
      {messages.map((message) => (
        <div key={message.id} className="flex">
          <MessageBubble message={message} />
        </div>
      ))}
    </div>
  );
}
