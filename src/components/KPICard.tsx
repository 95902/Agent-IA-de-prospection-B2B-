import { type LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";

export interface KpiCardProps {
  title: string;
  value: number | string;
  change: number;
  isPositive: boolean;
  icon: LucideIcon;
  iconTextColor: string;
  iconBackgroundColor: string;
}

export const KPICard = ({
  title,
  value,
  change,
  isPositive,
  icon: Icon,
  iconTextColor,
  iconBackgroundColor,
}: KpiCardProps) => {
  const TrendIcon = isPositive ? TrendingUp : TrendingDown;

  return (
    <Card className="duration-200 h-40 w-57.5 hover:-translate-y-1 rounded-xl border p-6 transition-all hover:shadow-md">
      <CardContent className="flex flex-col gap-4 p-0">
        <div className="flex justify-between">
          <div
            className={`flex h-12 w-12 items-center justify-center rounded-xl ${iconBackgroundColor} ${iconTextColor} `}
          >
            <Icon className="h-6 w-6" />
          </div>
          <div
            className={`flex mt-1 gap-1 font-semibold text-sm ${
              isPositive
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-rose-600 dark:text-rose-400"
            }`}
          >
            <TrendIcon className="h-4 w-4" />
            <span> {`${isPositive ? "+" : "-"}${change}%`}</span>
          </div>
        </div>
        <div className="">
          <p className="text-md text-[#45464D] tracking-wider leading-6  uppercase inter">
            {title}
          </p>
          <p className="text-[#1B1B1D] leading-6">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
};
