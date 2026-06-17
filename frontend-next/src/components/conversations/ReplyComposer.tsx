"use client";

import { useState } from "react";
import { Loader2, Send, Paperclip, Smile, Image as ImageIcon } from "lucide-react";

export function ReplyComposer({
  isPending,
  onSend,
}: {
  isPending: boolean;
  onSend: (text: string) => void;
}) {
  const [text, setText] = useState("");

  return (
    <div className="flex flex-col gap-3">
      <div className="relative">
        <textarea
          rows={3}
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Type your reply..."
          className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50/50 p-4 text-sm focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all custom-scrollbar pr-12"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (text.trim() && !isPending) {
                onSend(text);
                setText("");
              }
            }
          }}
        />
        <div className="absolute bottom-3 right-3 text-slate-400">
          <Smile className="size-5 hover:text-slate-600 cursor-pointer transition-colors" />
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1">
          <button className="flex size-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors">
            <Paperclip className="size-4" />
          </button>
          <button className="flex size-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors">
            <ImageIcon className="size-4" />
          </button>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 hidden sm:inline-block">Press Enter to send</span>
          <button
            onClick={() => {
              if (!text.trim()) {
                return;
              }
              onSend(text);
              setText("");
            }}
            disabled={isPending || !text.trim()}
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isPending ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Reply
          </button>
        </div>
      </div>
    </div>
  );
}
