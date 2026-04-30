import { Loader2 } from "lucide-react";

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center gap-3 rounded-2xl border border-slate-200 bg-white/70 text-slate-600 shadow-sm">
      <Loader2 className="size-4 animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  );
}
