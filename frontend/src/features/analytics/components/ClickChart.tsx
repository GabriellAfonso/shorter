import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import type { DailyClick, DeviceStat } from "@/types";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

interface DailyChartProps {
  data: DailyClick[];
}

export function DailyClicksChart({ data }: DailyChartProps) {
  const formatted = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    clicks: d.count,
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={formatted} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="clickGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} className="text-muted-foreground" />
        <YAxis allowDecimals={false} tick={{ fontSize: 11 }} className="text-muted-foreground" />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            borderColor: "hsl(var(--border))",
            borderRadius: 8,
          }}
          labelStyle={{ color: "hsl(var(--foreground))" }}
        />
        <Area
          type="monotone"
          dataKey="clicks"
          stroke="#3b82f6"
          fill="url(#clickGradient)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface DeviceChartProps {
  data: DeviceStat[];
}

export function DeviceChart({ data }: DeviceChartProps) {
  if (data.length === 0)
    return <p className="text-sm text-muted-foreground text-center py-8">No data yet.</p>;

  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="device_type"
          cx="50%"
          cy="50%"
          outerRadius={70}
          paddingAngle={4}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            borderColor: "hsl(var(--border))",
            borderRadius: 8,
          }}
        />
        <Legend formatter={(v) => <span className="text-xs capitalize">{v}</span>} />
      </PieChart>
    </ResponsiveContainer>
  );
}
