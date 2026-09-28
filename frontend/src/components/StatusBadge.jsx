import { Badge } from "@/components/ui/badge";
import { STATUS_STYLE } from "@/lib/factoryApi";

export function StatusBadge({ status, testId }) {
  return (
    <Badge
      data-testid={testId}
      variant="outline"
      className={`font-mono-x text-[10px] uppercase tracking-wide px-2 py-0.5 border ${STATUS_STYLE[status] || "bg-slate-500/10 text-slate-300 border-slate-500/25"}`}
    >
      {status}
    </Badge>
  );
}
