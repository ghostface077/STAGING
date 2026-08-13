"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { CountByLabel } from "@/lib/types";

// Couleurs pleines (non-Tailwind) correspondant aux teintes de STATUS_COLORS, pour le rendu SVG de recharts.
const STATUS_HEX: Record<string, string> = {
  "Nouveau": "#0ea5e9",
  "Ouvert": "#6366f1",
  "En cours": "#f59e0b",
  "En attente": "#fb923c",
  "Résolu": "#10b981",
  "Fermé": "#64748b",
  "Réouvert": "#a855f7",
  "Annulé": "#ef4444",
};

export function StatusBarChart({ data }: { data: CountByLabel[] }) {
  if (data.length === 0) {
    return <p className="flex h-64 items-center justify-center text-sm text-muted-foreground">Aucune donnée disponible.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <XAxis dataKey="label" tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} axisLine={{ stroke: "hsl(var(--border))" }} tickLine={false} />
        <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} />
        <Tooltip
          cursor={{ fill: "hsl(var(--muted))" }}
          contentStyle={{ borderRadius: 8, borderColor: "hsl(var(--border))", fontSize: 12, background: "hsl(var(--popover))", color: "hsl(var(--popover-foreground))" }}
          formatter={(value) => [`${value} ticket(s)`, "Total"]}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={48}>
          {data.map((entry) => (
            <Cell key={entry.label} fill={STATUS_HEX[entry.label] ?? "#64748b"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
