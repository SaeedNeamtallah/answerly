import { Loader2 } from "lucide-react";

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center gap-3 rounded-xl border border-border bg-card/80 text-muted-foreground shadow-sm">
      <Loader2 className="size-4 animate-spin text-primary" />
      <span className="text-sm">{label}</span>
    </div>
  );
}
