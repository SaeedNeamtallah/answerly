"use client";

import { FormEvent, useState } from "react";
import { Loader2, Send, Bot, User, Sparkles } from "lucide-react";

import type { QueryResponse } from "@/lib/types/query";
import { cn } from "@/lib/utils/cn";

export function TestChatPanel({
  onSubmit,
  isPending,
  result,
}: {
  onSubmit: (question: string) => void;
  isPending: boolean;
  result?: QueryResponse | null;
}) {
  const [question, setQuestion] = useState("");

  return (
    <div className="flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden h-[600px]">
      <div className="border-b border-slate-200 bg-slate-50/50 px-5 py-4 flex items-center justify-between">
        <h3 className="font-semibold text-slate-900 flex items-center gap-2">
          <Bot className="size-4 text-indigo-500" />
          Test Query
        </h3>
        {isPending && (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium ring-1 ring-inset bg-indigo-50 text-indigo-700 ring-indigo-200">
            <Loader2 className="size-3 animate-spin" /> Thinking...
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/30 custom-scrollbar">
        {result ? (
          <>
            <div className="flex gap-4 max-w-[85%] ml-auto flex-row-reverse">
              <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-500 shadow-sm">
                <User className="size-4" />
              </div>
              <div className="rounded-2xl rounded-tr-none bg-slate-200 px-5 py-3.5 text-sm text-slate-800 shadow-sm">
                <p className="whitespace-pre-wrap">{question || "Previous question"}</p>
              </div>
            </div>

            <div className="flex gap-4 max-w-[85%]">
              <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white shadow-sm">
                <Bot className="size-4" />
              </div>
              <div className="space-y-3 min-w-0">
                <div className="rounded-2xl rounded-tl-none border border-slate-200 bg-white px-5 py-3.5 text-sm text-slate-700 shadow-sm leading-relaxed">
                  <p className="whitespace-pre-wrap">{result.answer}</p>
                </div>
                
                {result.sources && result.sources.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    <span className="flex items-center gap-1 text-xs font-medium text-slate-500 mr-1">
                      <Sparkles className="size-3" /> Sources:
                    </span>
                    {result.sources.map((source, index) => (
                      <span key={`${source.document_name}-${index}`} className="inline-flex items-center px-2 py-1 rounded-md text-[10px] font-medium bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200/50 max-w-[200px] truncate">
                        {source.document_name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-3">
            <div className="flex size-12 items-center justify-center rounded-full bg-indigo-50 text-indigo-500">
              <Sparkles className="size-6" />
            </div>
            <div>
              <p className="font-medium text-slate-900">Start testing your knowledge base</p>
              <p className="text-sm text-slate-500 mt-1 max-w-xs mx-auto">Ask a question to see how the bot responds using your documents.</p>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-slate-200 bg-white">
        <form
          className="relative"
          onSubmit={(event: FormEvent<HTMLFormElement>) => {
            event.preventDefault();
            if (!question.trim() || isPending) {
              return;
            }
            onSubmit(question);
          }}
        >
          <textarea
            rows={3}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask a question..."
            className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50/50 p-4 text-sm focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all custom-scrollbar pr-28"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                if (question.trim() && !isPending) {
                  onSubmit(question);
                }
              }
            }}
          />
          <button
            type="submit"
            disabled={isPending || !question.trim()}
            className="absolute bottom-3 right-3 flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isPending ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}
