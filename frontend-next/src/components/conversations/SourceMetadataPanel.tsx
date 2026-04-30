import { ConversationMessage } from "@/lib/types/conversation";

export function SourceMetadataPanel({ message }: { message?: ConversationMessage | null }) {
  if (!message?.answer_sources_json?.length && !message?.retrieval_metadata_json) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm">
        No internal retrieval metadata for the selected message.
      </div>
    );
  }

  return (
    <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div>
        <p className="text-sm font-medium text-slate-900">Sources</p>
        <pre className="mt-2 overflow-x-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">
          {JSON.stringify(message.answer_sources_json, null, 2)}
        </pre>
      </div>
      <div>
        <p className="text-sm font-medium text-slate-900">Retrieval metadata</p>
        <pre className="mt-2 overflow-x-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">
          {JSON.stringify(message.retrieval_metadata_json, null, 2)}
        </pre>
      </div>
    </div>
  );
}
