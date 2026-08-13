import { AlertTriangle, CheckCircle2, Clock, XCircle } from "lucide-react";

import { Progress } from "@/components/ui/progress";
import { SLA_STATE_COLORS, SLA_STATE_LABELS, SLA_STATE_TEXT_COLORS } from "@/lib/constants";
import type { SLAProgress } from "@/lib/types";
import { cn, formatDurationMinutes } from "@/lib/utils";

const STATE_ICONS = {
  normal: CheckCircle2,
  attention: Clock,
  critique: AlertTriangle,
  depasse: XCircle,
  aucun: Clock,
} as const;

interface SlaIndicatorProps {
  progress: SLAProgress | null | undefined;
  compact?: boolean;
}

/** Indicateur visuel du respect du SLA d'un ticket : barre de progression + temps restant. */
export function SlaIndicator({ progress, compact = false }: SlaIndicatorProps) {
  if (!progress || progress.state === "aucun") {
    return <p className="text-sm text-muted-foreground">Aucun SLA associé à ce ticket.</p>;
  }

  const Icon = STATE_ICONS[progress.state];
  const percent = Math.min(progress.percent_elapsed ?? 0, 100);

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className={cn("flex items-center gap-1.5 font-medium", SLA_STATE_TEXT_COLORS[progress.state])}>
          <Icon className="h-4 w-4" />
          {SLA_STATE_LABELS[progress.state]}
        </span>
        {!compact && (
          <span className="text-muted-foreground">
            {progress.minutes_remaining !== null && progress.minutes_remaining >= 0
              ? `Temps restant : ${formatDurationMinutes(progress.minutes_remaining)}`
              : progress.minutes_remaining !== null
                ? `Dépassé de ${formatDurationMinutes(Math.abs(progress.minutes_remaining))}`
                : ""}
          </span>
        )}
      </div>
      <Progress value={percent} indicatorClassName={SLA_STATE_COLORS[progress.state]} />
    </div>
  );
}
