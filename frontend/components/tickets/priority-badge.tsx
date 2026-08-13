import { AlertTriangle } from "lucide-react";

import { PRIORITY_DOT_COLORS } from "@/lib/constants";
import { cn } from "@/lib/utils";

/** Badge de priorité : point coloré discret + libellé. La priorité Critique se distingue par une icône. */
export function PriorityBadge({ name, className }: { name: string; className?: string }) {
  const isCritical = name === "Critique";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        isCritical ? "border-destructive/30 bg-destructive/5 text-destructive" : "border-border bg-card text-foreground",
        className,
      )}
    >
      {isCritical ? (
        <AlertTriangle className="h-3 w-3 shrink-0" />
      ) : (
        <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", PRIORITY_DOT_COLORS[name] ?? "bg-muted-foreground")} />
      )}
      {name}
    </span>
  );
}
