/* eslint-disable react-refresh/only-export-components */
import { DesktopTable } from "@/components/DesktopTable";
import { KPICard, type KpiCardProps } from "@/components/KPICard";
import { useQuery } from "@tanstack/react-query";
import { getKpis, getProspects } from "@/lib/api";

import { createFileRoute } from "@tanstack/react-router";
import { HandCoins, Rocket, Users, Zap } from "lucide-react";
import { CampagneHealth } from "@/components/CampagneHealth";
import { HeaderPropspect } from "@/components/HeaderPropspect";
import { ChartProspect } from "@/components/ChartProspect";

export interface PropspectTableProps {
  id: string;
  companyName: string;
  contactName: string;
  contactRole: string;
  status: "Qualified" | "Discovery";
  score: number;
}

const Dashboard = () => {
  // KPIs réels (fenêtre 30 jours). Pas de `change` : aucune série temporelle.
  const { data: kpis } = useQuery({
    queryKey: ["kpis", { sinceDays: 30 }],
    queryFn: () => getKpis({ sinceDays: 30 }),
  });

  // Aperçu des meilleurs prospects (triés par score) pour la table du dashboard.
  const { data: page } = useQuery({
    queryKey: ["prospects", { limit: 10 }],
    queryFn: () => getProspects({ limit: 10 }),
  });
  const recentProspects: PropspectTableProps[] = (page?.items ?? []).map(
    (p) => ({
      id: p.id,
      companyName: p.nom_entreprise,
      contactName: p.telephone ?? p.email ?? "—",
      contactRole: p.code_naf ?? "—",
      status: p.statut === "qualifie" ? "Qualified" : "Discovery",
      score: p.score_final,
    }),
  );

  const kpiCards: KpiCardProps[] = [
    {
      title: "Prospects collectés",
      value: kpis?.collectes ?? "…",
      icon: Users,
      iconTextColor: "text-emerald-500",
      iconBackgroundColor: "bg-emerald-500/20",
    },
    {
      title: "Prospects qualifiés",
      value: kpis?.qualifies ?? "…",
      icon: Rocket,
      iconTextColor: "text-blue-500",
      iconBackgroundColor: "bg-blue-500/20",
    },
    {
      title: "Note moyenne (qualifiés)",
      value:
        kpis?.score_moy_qualifies != null
          ? `${kpis.score_moy_qualifies}/100`
          : "—",
      icon: Zap,
      iconTextColor: "text-amber-500",
      iconBackgroundColor: "bg-amber-500/20",
    },
    {
      title: "% qualifiés (≥60)",
      value: kpis != null ? `${kpis.pct_qualifies}%` : "…",
      icon: HandCoins,
      iconTextColor: "text-purple-500",
      iconBackgroundColor: "bg-purple-500/20",
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <HeaderPropspect />
      <div className="flex overflow-x-scroll gap-4 p-1">
        {kpiCards.map((kpi, index) => (
          <KPICard
            key={index}
            title={kpi.title}
            value={kpi.value}
            icon={kpi.icon}
            iconTextColor={kpi.iconTextColor}
            iconBackgroundColor={kpi.iconBackgroundColor}
          />
        ))}
      </div>
      <div className="flex flex-col w-full lg:flex-row gap-4">
        <ChartProspect />
        <CampagneHealth />
      </div>
      <DesktopTable data={recentProspects} />
    </div>
  );
};

export const Route = createFileRoute("/")({
  component: Dashboard,
});
