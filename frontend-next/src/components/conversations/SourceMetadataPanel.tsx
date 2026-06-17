import { ConversationMessage } from "@/lib/types/conversation";
import { Search, Database, FileText, Code2, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export function SourceMetadataPanel({ message }: { message?: ConversationMessage | null }) {
  if (!message?.answer_sources_json?.length && !message?.retrieval_metadata_json) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-6 text-sm text-slate-500 shadow-sm text-center">
        <Database className="size-6 text-slate-400 mx-auto mb-2" />
        No internal retrieval metadata for the selected message.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="border-b border-slate-200 bg-slate-50/50 px-5 py-4 flex items-center justify-between">
        <h3 className="font-semibold text-slate-900 flex items-center gap-2">
          <Search className="size-4 text-emerald-500" />
          Internal Retrieval
        </h3>
        {message.answer_sources_json?.length ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ring-1 ring-inset bg-emerald-50 text-emerald-700 ring-emerald-200">
            {message.answer_sources_json.length} Sources
          </span>
        ) : null}
      </div>
      <div className="p-5 space-y-6">
        <div className="space-y-3">
          <p className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <FileText className="size-4 text-slate-400" />
            Sources used
          </p>
          <div className="flex flex-col gap-2">
            {(message.answer_sources_json || []).map((source, index) => {
              const documentName = String(source.document_name || source.filename || `Source ${index + 1}`);
              const similarity = source.similarity === undefined ? null : Number(source.similarity);
              const similarityText = similarity === null || !Number.isFinite(similarity) ? null : similarity.toFixed(3);
              const isHighConfidence = similarity && similarity > 0.8;
              
              return (
                <div key={`${documentName}-${index}`} className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="size-4 text-indigo-500 shrink-0" />
                    <span className="truncate text-sm font-medium text-slate-700">{documentName}</span>
                  </div>
                  {similarityText && (
                    <span className={cn(
                      "shrink-0 inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium",
                      isHighConfidence ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-700"
                    )}>
                      {similarityText}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
        
        {message.retrieval_metadata_json ? (
          <div className="space-y-3">
            <p className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <Code2 className="size-4 text-slate-400" />
              Retrieval metadata
            </p>
            <div className="space-y-2">
              {Object.entries(message.retrieval_metadata_json).map(([key, value]) => (
                <div key={key} className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm">
                  <p className="font-medium text-slate-900 capitalize flex items-center gap-2">
                    <span className="size-1.5 rounded-full bg-indigo-500" />
                    {key.replace(/_/g, " ")}
                  </p>
                  <p className="mt-1.5 break-words text-xs text-slate-500 font-mono bg-slate-50 p-2 rounded-lg border border-slate-100">
                    {typeof value === "object" ? JSON.stringify(value) : String(value)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
