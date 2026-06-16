"use client";

import { useState } from "react";
import { Loader2, Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export function ReplyComposer({
  isPending,
  onSend,
}: {
  isPending: boolean;
  onSend: (text: string) => void;
}) {
  const [text, setText] = useState("");

  return (
    <Card className="border-border/80 bg-card shadow-sm">
      <CardHeader>
        <CardTitle className="text-base">Manual reply</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Textarea
          rows={4}
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Send a manual reply"
        />
        <Button
          onClick={() => {
            if (!text.trim()) {
              return;
            }
            onSend(text);
            setText("");
          }}
          disabled={isPending}
        >
          {isPending ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          Reply
        </Button>
      </CardContent>
    </Card>
  );
}
