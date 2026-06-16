import { ConversationMessage } from "@/lib/types/conversation";

import { EmptyState } from "@/components/shared/EmptyState";
import { MessageBubble } from "@/components/conversations/MessageBubble";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ConversationThread({ messages }: { messages: ConversationMessage[] }) {
  if (messages.length === 0) {
    return <EmptyState title="No messages" description="This conversation does not have messages yet." />;
  }

  return (
    <Card className="border-border/80 bg-card shadow-sm">
      <CardHeader>
        <CardTitle className="text-base">Thread</CardTitle>
      </CardHeader>
      <CardContent className="max-h-[620px] space-y-3 overflow-y-auto bg-muted/30 p-4">
        {messages.map((message) => (
          <div key={message.id} className="flex">
            <MessageBubble message={message} />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
