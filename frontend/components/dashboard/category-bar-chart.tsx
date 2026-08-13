"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { CountByLabel } from "@/lib/types";

/** Diagramme en barres horizontal, une seule teinte (mesure de grandeur, pas d'identité à distinguer). */
export function CategoryBarChart({ data }: { data: CountByLabel[] }) {
  if (data.length === 0) {
    return <p className="flex h-64 items-center justify-center text-sm text-muted-foreground">Aucune donnée disponible.</p>;
  }

  const sorted = [...data].sort((a, b) => b.count - a.count).slice(0, 8);

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, sorted.length * 36)}>
      <BarChart data={sorted} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid horizontal={false} stroke="hsl(var(--border))" />
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="label"
          width={140}
          tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: "hsl(var(--muted))" }}
          contentStyle={{ borderRadius: 8, borderColor: "hsl(var(--border))", fontSize: 12, background: "hsl(var(--popover))", color: "hsl(var(--popover-foreground))" }}
          formatter={(value) => [`${value} ticket(s)`, "Total"]}
        />
        <Bar dataKey="count" fill="#2a78d6" radius={[0, 4, 4, 0]} maxBarSize={20} />
      </BarChart>
    </ResponsiveContainer>
  );
}
