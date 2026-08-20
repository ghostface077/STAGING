"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Clock, XCircle } from "lucide-react";

import { SLA_STATE_LABELS, SLA_STATE_STROKE_COLORS, SLA_STATE_TEXT_COLORS } from "@/lib/constants";
import type { SLAProgress } from "@/lib/types";
import { cn, formatDateTime, formatDurationMinutes } from "@/lib/utils";

const STATE_ICONS = {
  normal: CheckCircle2,
  attention: Clock,
  critique: AlertTriangle,
  depasse: XCircle,
  aucun: Clock,
} as const;

const SIZE = 132;
const STROKE = 10;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

interface SlaGaugeProps {
  progress: SLAProgress | null | undefined;
}

/** Jauge circulaire du respect du SLA d'un ticket, avec le détail des deux échéances (1ère réponse / résolution). */
export function SlaGauge({ progress }: SlaGaugeProps) {
  if (!progress || progress.state === "aucun") {
    return <p className="text-sm text-muted-foreground">Aucun SLA associé à ce ticket.</p>;
  }

  const Icon = STATE_ICONS[progress.state];
  const percent = Math.min(Math.max(progress.percent_elapsed ?? 0, 0), 100);
  const stroke = SLA_STATE_STROKE_COLORS[progress.state];
  const timeLabel =
    progress.minutes_remaining !== null && progress.minutes_remaining >= 0
      ? `${formatDurationMinutes(progress.minutes_remaining)} restantes`
      : progress.minutes_remaining !== null
        ? `Dépassé de ${formatDurationMinutes(Math.abs(progress.minutes_remaining))}`
        : "—";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center">
        <div className="relative" style={{ width: SIZE, height: SIZE }}>
          <svg width={SIZE} height={SIZE} className="-rotate-90">
            <circle cx={SIZE / 2} cy={SIZE / 2} r={RADIUS} fill="none" stroke="hsl(var(--muted))" strokeWidth={STROKE} />
            <motion.circle
              cx={SIZE / 2}
              cy={SIZE / 2}
              r={RADIUS}
              fill="none"
              stroke={stroke}
              strokeWidth={STROKE}
              strokeLinecap="round"
              strokeDasharray={CIRCUMFERENCE}
              initial={{ strokeDashoffset: CIRCUMFERENCE }}
              animate={{ strokeDashoffset: CIRCUMFERENCE * (1 - percent / 100) }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5">
            <Icon className={cn("h-5 w-5", SLA_STATE_TEXT_COLORS[progress.state])} />
            <span className="text-lg font-semibold tabular-nums">{Math.round(percent)}%</span>
          </div>
        </div>
      </div>

      <div className="text-center">
        <p className={cn("text-sm font-medium", SLA_STATE_TEXT_COLORS[progress.state])}>{SLA_STATE_LABELS[progress.state]}</p>
        <p className="text-xs text-muted-foreground">{timeLabel}</p>
      </div>

      <div className="space-y-2 border-t border-border pt-3 text-xs">
        <MilestoneRow
          label="1ère réponse"
          met={progress.first_response_met}
          deadline={progress.first_response_deadline}
        />
        <MilestoneRow label="Résolution" met={null} deadline={progress.resolution_deadline} />
      </div>
    </div>
  );
}

function MilestoneRow({ label, met, deadline }: { label: string; met: boolean | null; deadline: string | null }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="flex items-center gap-1.5 text-muted-foreground">
        {met === true && <CheckCircle2 className="h-3.5 w-3.5 text-success" />}
        {label}
      </span>
      <span className="font-medium">{deadline ? formatDateTime(deadline) : "—"}</span>
    </div>
  );
}
