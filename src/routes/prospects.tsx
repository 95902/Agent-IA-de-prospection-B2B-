/* eslint-disable react-refresh/only-export-components */
import { KPICard, type KpiCardProps } from "@/components/KPICard";
import { createFileRoute } from "@tanstack/react-router";
import { CircleEuro, HandCoins, Users, Zap } from "lucide-react";

//THEME
//SEED
//STATE

const KPICardSeed: KpiCardProps[] = [
  {
    title: "Total des prospects",
    value: "14,282",
    change: 12.5,
    isPositive: true,
    icon: Users,
    iconTextColor: "text-emerald-500",
    iconBackgroundColor: "bg-emerald-500/20",
  },
  {
    title: "Valeur du pipeline",
    value: "2.4M€",
    change: 8.1,
    isPositive: true,
    icon: CircleEuro,
    iconTextColor: "text-blue-500",
    iconBackgroundColor: "bg-blue-500/20",
  },
  {
    title: "Note moyenne",
    value: "84/100",
    change: 2.4,
    isPositive: false,
    icon: Zap,
    iconTextColor: "text-red-500",
    iconBackgroundColor: "bg-red-500/20",
  },
  {
    title: "Taux de conversion",
    value: "4.2%",
    change: 18.3,
    isPositive: true,
    icon: HandCoins ,
    iconTextColor: "text-purple-500",
    iconBackgroundColor: "bg-purple-500/20",
  },
];

const Prospects = () => {
  return (
    <div className="flex flex-wrap gap-4">
      {KPICardSeed.map((kpi, index) => (
        <KPICard
          key={index}
          title={kpi.title}
          value={kpi.value}
          change={kpi.change}
          isPositive={kpi.isPositive}
          icon={kpi.icon}
          iconTextColor={kpi.iconTextColor}
          iconBackgroundColor={kpi.iconBackgroundColor}
        />
      ))}
    </div>
  );
};

export const Route = createFileRoute("/prospects")({
  component: Prospects,
});
