"use client";

import { FormEvent, useState } from "react";
import { Loader2, Send } from "lucide-react";

import type { QueryResponse } from "@/lib/types/query";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

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
    <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-950">Test chat</h3>
        <p className="text-sm text-slate-600">Uses the supported non-streaming project query endpoint.</p>
      </div>
      <form
        className="space-y-3"
        onSubmit={(event: FormEvent<HTMLFormElement>) => {
          event.preventDefault();
          if (!question.trim()) {
            return;
          }
          onSubmit(question);
        }}
      >
        <Textarea
          rows={4}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about this knowledge base"
        />
        <Button type="submit" disabled={isPending}>
          {isPending ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          Ask
        </Button>
      </form>
      {result ? (
        <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="whitespace-pre-wrap text-sm text-slate-800">{result.answer}</p>
          <div className="space-y-1 text-xs text-slate-500">
            {(result.sources || []).map((source, index) => (
              <p key={`${source.document_name}-${index}`}>
                {source.document_name} · chunk {source.chunk_index} · similarity {source.similarity.toFixed(3)}
              </p>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
