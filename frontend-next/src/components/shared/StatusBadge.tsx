import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";
import { formatStatusLabel, getStatusVariant } from "@/lib/utils/status";

const styles = {
  default: "border-border bg-muted text-muted-foreground",
  secondary: "border-border bg-secondary text-secondary-foreground",
  success: "border-emerald-200 bg-emerald-50 text-emerald-700",
  warning: "border-amber-200 bg-amber-50 text-amber-700",
  danger: "border-rose-200 bg-rose-50 text-rose-700",
};

export function StatusBadge({ status }: { status?: string | null }) {
  const variant = getStatusVariant(status);

  return (
    <Badge className={cn("h-6 rounded-md px-2 text-xs font-medium capitalize", styles[variant])}>
      {formatStatusLabel(status)}
    </Badge>
  );
}
