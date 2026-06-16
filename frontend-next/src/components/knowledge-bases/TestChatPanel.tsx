"use client";

import { FormEvent, useState } from "react";
import { Loader2, Send } from "lucide-react";

import type { QueryResponse } from "@/lib/types/query";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
    <Card className="border-border/80 bg-card shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Send className="size-4" />
          </span>
          Test chat
        </CardTitle>
        <p className="text-sm text-muted-foreground">Uses the supported non-streaming project query endpoint.</p>
      </CardHeader>
      <CardContent className="space-y-4">
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
        <div className="space-y-3 rounded-xl border bg-muted/40 p-4">
          <p className="whitespace-pre-wrap text-sm leading-6 text-foreground">{result.answer}</p>
          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
            {(result.sources || []).map((source, index) => (
              <Badge key={`${source.document_name}-${index}`} variant="outline" className="rounded-md">
                {source.document_name} · chunk {source.chunk_index} · similarity {source.similarity.toFixed(3)}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}
      </CardContent>
    </Card>
  );
}
