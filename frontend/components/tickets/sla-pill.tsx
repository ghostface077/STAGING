import { AlertTriangle, CheckCircle2, Clock, XCircle } from "lucide-react";

import { SLA_STATE_TEXT_COLORS } from "@/lib/constants";
import type { SLAProgress } from "@/lib/types";
import { cn, formatDurationMinutes } from "@/lib/utils";

const STATE_ICONS = {
  normal: CheckCircle2,
  attention: Clock,
  critique: AlertTriangle,
  depasse: XCircle,
  aucun: Clock,
} as const;

/** Version compacte de l'indicateur SLA, pour les tableaux (listes de tickets). */
export function SlaPill({ progress }: { progress: SLAProgress | null | undefined }) {
  if (!progress || progress.state === "aucun") {
    return <span className="text-xs text-muted-foreground">—</span>;
  }

  const Icon = STATE_ICONS[progress.state];
  const label =
    progress.minutes_remaining !== null && progress.minutes_remaining >= 0
      ? `${formatDurationMinutes(progress.minutes_remaining)} restantes`
      : progress.minutes_remaining !== null
        ? `Dépassé de ${formatDurationMinutes(Math.abs(progress.minutes_remaining))}`
        : "—";

  return (
    <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap text-xs font-medium", SLA_STATE_TEXT_COLORS[progress.state])}>
      <Icon className="h-3.5 w-3.5 shrink-0" />
      {label}
    </span>
  );
}
