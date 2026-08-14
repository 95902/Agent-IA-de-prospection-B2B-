"use client";

import { Area, AreaChart, CartesianGrid, XAxis } from "recharts";

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

export const description = "An area chart with a legend";

const chartData = [
  { month: "January", desktop: 186, mobile: 80 },
  { month: "February", desktop: 305, mobile: 200 },
  { month: "March", desktop: 237, mobile: 120 },
  { month: "April", desktop: 73, mobile: 190 },
  { month: "May", desktop: 209, mobile: 130 },
  { month: "June", desktop: 214, mobile: 140 },
];

const chartConfig = {
  desktop: {
    label: "Desktop",
    color: "var(--chart-1)",
  },
  mobile: {
    label: "Mobile",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig;

export function ChartProspect() {
  return (
    <Card className="flex-1 rounded-lg">
      <CardHeader>
        <div className="flex items-center justify-between pt-4">
          <div className="flex flex-col">
            <CardTitle>Diriger l'évolution</CardTitle>
            <CardDescription>
              Croissance projetée contre croissance réelle au fil du temps
            </CardDescription>
          </div>
          <div className="flex items-center space-x-3">
            <div className="h-4 w-4 rounded-xs bg-[#316BF3]" /> <p>Actuel</p>
            <div className="h-4 w-4 rounded-xs bg-[#64748b]/50" /> <p>Cible</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig}>
          <AreaChart
            accessibilityLayer
            data={chartData}
            margin={{
              left: 12,
              right: 12,
            }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="month"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              tickFormatter={(value) => value.slice(0, 3)}
            />
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent indicator="line" />}
            />
            <Area
              dataKey="mobile"
              type="natural"
              fill="white"
              strokeWidth={2.5}
              stroke="#64748b"
              strokeDasharray="4 4"
            />
            <Area
              dataKey="desktop"
              type="natural"
              fill="white"
              strokeWidth={2.5}
              stroke="#316BF3"
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
