"use client";

import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { titleCase } from "@/lib/utils";

const PALETTE = [
  "#087F8C", // Professional Teal
  "#203A4A", // Dark Slate
  "#142B3B", // Deep Navy
  "#D97706", // Amber
  "#0D9488", // Teal Dark
  "#4F46E5", // Indigo
  "#E11D48", // Rose
  "#059669", // Emerald
  "#0284C7", // Sky
  "#7C3AED", // Violet
];

const tooltipStyle = {
  backgroundColor: "#FFFFFF",
  border: "1px solid #E4EAE9",
  borderRadius: 6,
  fontSize: 12,
  color: "#192D38",
  boxShadow: "0 4px 6px -1px rgba(20, 43, 59, 0.08)",
  padding: "8px 12px",
};

export function TrendChart({
  points,
}: {
  points: { date: string; complaints: number; reports: number }[];
}) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E4EAE9" vertical={false} />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#71818A" }}
                 tickFormatter={(v: string) => v.slice(5)} stroke="#E4EAE9" />
          <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#71818A" }} stroke="#E4EAE9" />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
          <Line type="monotone" dataKey="complaints" name="Civic Complaints" stroke="#087F8C"
                strokeWidth={2.5} dot={false} activeDot={{ r: 4, fill: "#087F8C" }} />
          <Line type="monotone" dataKey="reports" name="Clinical Symptoms" stroke="#D97706"
                strokeWidth={2.5} dot={false} activeDot={{ r: 4, fill: "#D97706" }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CategoryPie({ data }: { data: Record<string, number> }) {
  const rows = Object.entries(data).map(([name, value]) => ({ name: titleCase(name), value }));
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={rows} dataKey="value" nameKey="name" innerRadius={48} outerRadius={82}
               paddingAngle={2}>
            {rows.map((_, i) => (
              <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SimpleBarChart({
  data, color = "#087F8C", horizontal = false,
}: {
  data: { name: string; value: number }[];
  color?: string;
  horizontal?: boolean;
}) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={{ top: 8, right: 12, left: horizontal ? 40 : -18, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E4EAE9" vertical={false} />
          {horizontal ? (
            <>
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: "#71818A" }} stroke="#E4EAE9" />
              <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 11, fill: "#71818A" }} stroke="#E4EAE9" />
            </>
          ) : (
            <>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#71818A" }}
                     tickFormatter={(v: string) => (v.length > 10 ? `${v.slice(0, 9)}…` : v)} stroke="#E4EAE9" />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#71818A" }} stroke="#E4EAE9" />
            </>
          )}
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey="value" fill={color} radius={horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]} maxBarSize={36} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
