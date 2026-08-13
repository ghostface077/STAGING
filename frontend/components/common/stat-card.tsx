import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  tone?: "default" | "success" | "warning" | "destructive" | "info" | "brand";
  hint?: string;
  size?: "default" | "lg";
}

const TONE_STYLES: Record<NonNullable<StatCardProps["tone"]>, string> = {
  default: "bg-primary/10 text-primary",
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
  destructive: "bg-destructive/10 text-destructive",
  info: "bg-info/10 text-info",
  brand: "bg-brand/10 text-brand",
};

/** Carte de statistique pour les tableaux de bord. `size="lg"` pour les indicateurs clés en tête de page. */
export function StatCard({ label, value, icon: Icon, tone = "default", hint, size = "default" }: StatCardProps) {
  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardContent className={cn("flex items-center gap-4", size === "lg" ? "p-5" : "p-4")}>
        <div
          className={cn(
            "flex shrink-0 items-center justify-center rounded-xl",
            TONE_STYLES[tone],
            size === "lg" ? "h-12 w-12" : "h-11 w-11",
          )}
        >
          <Icon className={size === "lg" ? "h-6 w-6" : "h-5 w-5"} />
        </div>
        <div className="min-w-0">
          <p className="truncate text-xs font-medium text-muted-foreground">{label}</p>
          <p className={cn("font-semibold tabular-nums leading-tight", size === "lg" ? "text-3xl" : "text-2xl")}>{value}</p>
          {hint && <p className="truncate text-xs text-muted-foreground">{hint}</p>}
        </div>
      </CardContent>
    </Card>
  );
}
