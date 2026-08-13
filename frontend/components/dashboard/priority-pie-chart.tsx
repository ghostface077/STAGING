"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { CountByLabel } from "@/lib/types";

const PRIORITY_HEX: Record<string, string> = {
  "Basse": "#94a3b8",
  "Normale": "#2a78d6",
  "Haute": "#f59e0b",
  "Critique": "#e34948",
};

export function PriorityPieChart({ data }: { data: CountByLabel[] }) {
  if (data.length === 0) {
    return <p className="flex h-64 items-center justify-center text-sm text-muted-foreground">Aucune donnée disponible.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={data} dataKey="count" nameKey="label" innerRadius={55} outerRadius={90} paddingAngle={2} strokeWidth={2} stroke="hsl(var(--card))">
          {data.map((entry) => (
            <Cell key={entry.label} fill={PRIORITY_HEX[entry.label] ?? "#94a3b8"} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ borderRadius: 8, borderColor: "hsl(var(--border))", fontSize: 12, background: "hsl(var(--popover))", color: "hsl(var(--popover-foreground))" }}
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
