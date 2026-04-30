"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
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
    <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
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
        {isPending ? <Loader2 className="size-4 animate-spin" /> : null}
        Reply
      </Button>
    </div>
  );
}
