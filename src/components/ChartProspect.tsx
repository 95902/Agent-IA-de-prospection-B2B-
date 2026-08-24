"use client";

import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { useQuery } from "@tanstack/react-query";
import { getProspects } from "@/lib/api";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/Chart";

const BINS = [
  { label: "0-19", min: 0, max: 19 },
  { label: "20-39", min: 20, max: 39 },
  { label: "40-59", min: 40, max: 59 },
  { label: "60-79", min: 60, max: 79 },
  { label: "80-100", min: 80, max: 100 },
];

const chartConfig = {
  count: { label: "Prospects", color: "var(--chart-1)" },
} satisfies ChartConfig;

export function ChartProspect() {
  // Distribution réelle des score_final (2 pages pour couvrir jusqu'à 400).
  const { data } = useQuery({
    queryKey: ["prospects-distribution"],
    queryFn: async () => {
      const [a, b] = await Promise.all([
        getProspects({ limit: 200, offset: 0 }),
        getProspects({ limit: 200, offset: 200 }),
      ]);
      const items = [...a.items, ...b.items];
      return BINS.map((bin) => ({
        range: bin.label,
        count: items.filter(
          (p) => p.score_final >= bin.min && p.score_final <= bin.max,
        ).length,
      }));
    },
  });

  return (
    <Card className="flex-1 rounded-lg">
      <CardHeader>
        <div className="flex flex-col pt-4">
          <CardTitle>Distribution des scores</CardTitle>
          <CardDescription>
            Répartition des prospects par tranche de score (qualifié ≥ 60)
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig}>
          <BarChart
            accessibilityLayer
            data={data ?? []}
            margin={{ left: 12, right: 12 }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="range"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              width={28}
              allowDecimals={false}
            />
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent indicator="line" />}
            />
            <Bar dataKey="count" fill="var(--chart-1)" radius={4} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
