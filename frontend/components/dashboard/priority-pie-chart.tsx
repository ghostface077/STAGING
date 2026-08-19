"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { CountByLabel } from "@/lib/types";

// Miroir de PRIORITY_DOT_COLORS (lib/constants.ts) — une priorité a la même
// couleur ici que sur ses badges.
const PRIORITY_HEX: Record<string, string> = {
  "Basse": "hsl(var(--muted-foreground))",
  "Normale": "hsl(var(--info))",
  "Haute": "hsl(var(--warning))",
  "Critique": "hsl(var(--destructive))",
};

export function PriorityPieChart({ data }: { data: CountByLabel[] }) {
  if (data.length === 0) {
    return <p className="flex h-64 items-center justify-center text-sm text-muted-foreground">Aucune donnée disponible.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="label"
          innerRadius={55}
          outerRadius={90}
          paddingAngle={2}
          strokeWidth={2}
          stroke="hsl(var(--card))"
          animationDuration={500}
          animationEasing="ease-out"
        >
          {data.map((entry) => (
            <Cell key={entry.label} fill={PRIORITY_HEX[entry.label] ?? "hsl(var(--muted-foreground))"} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            borderRadius: 8,
            borderColor: "hsl(var(--border))",
            fontSize: 12,
            background: "hsl(var(--popover))",
            color: "hsl(var(--popover-foreground))",
            boxShadow: "0 4px 16px hsl(var(--shadow-color) / 0.10), 0 1px 2px hsl(var(--shadow-color) / 0.06)",
          }}
          formatter={(value, label) => [`${value} ticket(s)`, label]}
        />
        <Legend
          verticalAlign="bottom"
          height={32}
          iconType="circle"
          iconSize={8}
          formatter={(value) => <span className="text-xs text-muted-foreground">{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
