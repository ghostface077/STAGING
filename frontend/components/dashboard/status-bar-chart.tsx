"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { CountByLabel } from "@/lib/types";

// Miroir de STATUS_DOT_COLORS (lib/constants.ts), exprimé en valeurs CSS
// exploitables par Recharts (les tokens du design system, pas des teintes
// arbitraires) — un statut a la même couleur ici que sur ses badges.
const STATUS_HEX: Record<string, string> = {
  "Nouveau": "hsl(var(--info))",
  "Ouvert": "hsl(var(--primary))",
  "En cours": "hsl(var(--warning))",
  "En attente": "#f97316", // Tailwind orange-500, comme bg-orange-500 ailleurs
  "Résolu": "hsl(var(--success))",
  "Fermé": "hsl(var(--muted-foreground))",
  "Réouvert": "#d946ef", // Tailwind fuchsia-500, comme bg-fuchsia-500 ailleurs
  "Annulé": "hsl(var(--destructive))",
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
          contentStyle={{
            borderRadius: 8,
            borderColor: "hsl(var(--border))",
            fontSize: 12,
            background: "hsl(var(--popover))",
            color: "hsl(var(--popover-foreground))",
            boxShadow: "0 4px 16px hsl(var(--shadow-color) / 0.10), 0 1px 2px hsl(var(--shadow-color) / 0.06)",
          }}
          formatter={(value) => [`${value} ticket(s)`, "Total"]}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={48} animationDuration={500} animationEasing="ease-out">
          {data.map((entry) => (
            <Cell key={entry.label} fill={STATUS_HEX[entry.label] ?? "hsl(var(--muted-foreground))"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
