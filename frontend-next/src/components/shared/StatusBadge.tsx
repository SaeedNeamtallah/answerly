import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";
import { formatStatusLabel, getStatusVariant } from "@/lib/utils/status";

const styles = {
  default: "bg-slate-100 text-slate-700",
  secondary: "bg-slate-200 text-slate-800",
  success: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-700",
  danger: "bg-rose-100 text-rose-700",
};

export function StatusBadge({ status }: { status?: string | null }) {
  const variant = getStatusVariant(status);

  return (
    <Badge className={cn("border-transparent capitalize", styles[variant])}>
      {formatStatusLabel(status)}
    </Badge>
  );
}
