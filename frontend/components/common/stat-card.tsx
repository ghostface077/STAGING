"use client";

import { motion, animate, useMotionValue } from "framer-motion";
import { useEffect, useState } from "react";
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

/**
 * Affiche un nombre avec un comptage progressif à l'apparition. N'anime que
 * les valeurs numériques : une chaîne déjà formatée (ex. "4,2/5", "—") reste
 * affichée telle quelle par StatCard, sans passer par ce composant.
 */
function AnimatedNumber({ value }: { value: number }) {
  const [display, setDisplay] = useState(0);
  const motionValue = useMotionValue(0);

  useEffect(() => {
    const controls = animate(motionValue, value, {
      duration: 0.6,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => setDisplay(Math.round(v)),
    });
    return controls.stop;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return <>{display.toLocaleString("fr-FR")}</>;
}

/** Carte de statistique pour les tableaux de bord. `size="lg"` pour les indicateurs clés en tête de page. */
export function StatCard({ label, value, icon: Icon, tone = "default", hint, size = "default" }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -2 }}
    >
      <Card className="shadow-premium-sm transition-shadow duration-200 ease-premium hover:shadow-premium-md">
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
            <p className={cn("font-semibold tabular-nums leading-tight", size === "lg" ? "text-3xl" : "text-2xl")}>
              {typeof value === "number" ? <AnimatedNumber value={value} /> : value}
            </p>
            {hint && <p className="truncate text-xs text-muted-foreground">{hint}</p>}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
