import { STATUS_DOT_COLORS } from "@/lib/constants";
import { cn } from "@/lib/utils";

/** Badge de statut : point coloré discret + libellé, sur fond neutre (identité visuelle sobre). */
export function StatusBadge({ name, className }: { name: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-0.5 text-xs font-medium text-foreground",
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", STATUS_DOT_COLORS[name] ?? "bg-muted-foreground")} />
      {name}
    </span>
  );
}
