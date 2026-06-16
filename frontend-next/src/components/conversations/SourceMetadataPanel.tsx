import { ConversationMessage } from "@/lib/types/conversation";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function SourceMetadataPanel({ message }: { message?: ConversationMessage | null }) {
  if (!message?.answer_sources_json?.length && !message?.retrieval_metadata_json) {
    return (
      <div className="rounded-xl border bg-card p-4 text-sm text-muted-foreground shadow-sm">
        No internal retrieval metadata for the selected message.
      </div>
    );
  }

  return (
    <Card className="border-border/80 bg-card shadow-sm">
      <CardHeader>
        <CardTitle className="text-base">Internal Retrieval</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm font-medium text-foreground">Sources</p>
          <div className="flex flex-wrap gap-2">
            {(message.answer_sources_json || []).map((source, index) => {
              const documentName = String(source.document_name || source.filename || `Source ${index + 1}`);
              const similarity = source.similarity === undefined ? null : Number(source.similarity);
              const similarityText = similarity === null || !Number.isFinite(similarity) ? null : similarity.toFixed(3);
              return (
                <Badge key={`${documentName}-${index}`} variant="outline" className="h-auto rounded-md py-1">
                  {documentName}
                  {similarityText ? ` · ${similarityText}` : null}
                </Badge>
              );
            })}
          </div>
        </div>
        {message.retrieval_metadata_json ? (
          <div className="space-y-2">
            <p className="text-sm font-medium text-foreground">Retrieval metadata</p>
            <div className="space-y-2">
              {Object.entries(message.retrieval_metadata_json).map(([key, value]) => (
                <div key={key} className="rounded-lg border bg-background px-3 py-2 text-sm">
                  <p className="font-medium capitalize text-foreground">{key.replace(/_/g, " ")}</p>
                  <p className="mt-1 break-words text-xs text-muted-foreground">
                    {typeof value === "object" ? JSON.stringify(value) : String(value)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
