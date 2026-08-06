/* eslint-disable react-refresh/only-export-components */
import { DesktopTable } from "@/components/DesktopTable";
import { KPICard, type KpiCardProps } from "@/components/KPICard";

import { createFileRoute } from "@tanstack/react-router";
import {
  Building2,
  CircleEuro,
  Cloud,
  HandCoins,
  Rocket,
  Shield,
  Users,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { CampagneHealth } from "@/components/CampagneHealth";
import { HeaderPropspect } from "@/components/HeaderPropspect";
import { ChartProspect } from "@/components/ChartProspect";

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
    icon: HandCoins,
    iconTextColor: "text-purple-500",
    iconBackgroundColor: "bg-purple-500/20",
  },
];

export interface PropspectTableProps {
  id: string;
  companyName: string;
  contactName: string;
  contactRole: string;
  status: "Qualified" | "Negotiation" | "High Priority" | "Discovery";
  score: number;
  value: number; // Ou "$42,000" sous forme de string si tu préfères ne pas la formater
  logo: LucideIcon;
  logoBgColor: string;
  logoTextColor: string;
}
export const PropspectTableSeed: PropspectTableProps[] = [
  {
    id: "1",
    companyName: "Lumina Systems",
    contactName: "Sarah Jenkins",
    contactRole: "CTO",
    status: "Qualified",
    score: 2,
    value: 42000,
    logo: Building2,
    logoBgColor: "bg-slate-900 dark:bg-slate-800",
    logoTextColor: "text-white",
  },
  {
    id: "2",
    companyName: "Skyward Cloud",
    contactName: "Marcus Thorne",
    contactRole: "Head of Ops",
    status: "Negotiation",
    score: 78,
    value: 115000,
    logo: Cloud,
    logoBgColor: "bg-blue-100 dark:bg-blue-950",
    logoTextColor: "text-blue-600 dark:text-blue-400",
  },
  {
    id: "3",
    companyName: "Ironclad Security",
    contactName: "David Wu",
    contactRole: "Lead Architect",
    status: "High Priority",
    score: 85,
    value: 28500,
    logo: Shield,
    logoBgColor: "bg-emerald-100 dark:bg-emerald-950",
    logoTextColor: "text-emerald-600 dark:text-emerald-400",
  },
  {
    id: "4",
    companyName: "Velox Logistics",
    contactName: "Elena Costa",
    contactRole: "VP Logistics",
    status: "Discovery",
    score: 61,
    value: 12000,
    logo: Rocket,
    logoBgColor: "bg-indigo-100 dark:bg-indigo-950",
    logoTextColor: "text-indigo-600 dark:text-indigo-400",
  },
  {
    id: "5",
    companyName: "Apex Retail",
    contactName: "Alexandre Martin",
    contactRole: "Product Manager",
    status: "Qualified",
    score: 88,
    value: 64000,
    logo: Building2,
    logoBgColor: "bg-amber-100 dark:bg-amber-950",
    logoTextColor: "text-amber-600 dark:text-amber-400",
  },
  {
    id: "6",
    companyName: "Nova Analytics",
    contactName: "Camille Bernard",
    contactRole: "Data Lead",
    status: "Discovery",
    score: 55,
    value: 18000,
    logo: Cloud,
    logoBgColor: "bg-sky-100 dark:bg-sky-950",
    logoTextColor: "text-sky-600 dark:text-sky-400",
  },
  {
    id: "7",
    companyName: "Pulse Health",
    contactName: "Thomas Leroy",
    contactRole: "COO",
    status: "Negotiation",
    score: 91,
    value: 95000,
    logo: Shield,
    logoBgColor: "bg-rose-100 dark:bg-rose-950",
    logoTextColor: "text-rose-600 dark:text-rose-400",
  },
  {
    id: "8",
    companyName: "Quantum Dynamics",
    contactName: "Sophie Moreau",
    contactRole: "VP Engineering",
    status: "High Priority",
    score: 79,
    value: 34000,
    logo: Rocket,
    logoBgColor: "bg-purple-100 dark:bg-purple-950",
    logoTextColor: "text-purple-600 dark:text-purple-400",
  },
  {
    id: "9",
    companyName: "Zenith Media",
    contactName: "Lucas Petit",
    contactRole: "CMO",
    status: "Qualified",
    score: 73,
    value: 52000,
    logo: Building2,
    logoBgColor: "bg-slate-100 dark:bg-slate-800",
    logoTextColor: "text-slate-800 dark:text-slate-200",
  },
  {
    id: "10",
    companyName: "CyberShield Tech",
    contactName: "Emma Roux",
    contactRole: "CISO",
    status: "High Priority",
    score: 96,
    value: 140000,
    logo: Shield,
    logoBgColor: "bg-emerald-100 dark:bg-emerald-950",
    logoTextColor: "text-emerald-600 dark:text-emerald-400",
  },
  {
    id: "11",
    companyName: "AeroSpace Lab",
    contactName: "Gabriel Fournier",
    contactRole: "R&D Lead",
    status: "Negotiation",
    score: 82,
    value: 78000,
    logo: Rocket,
    logoBgColor: "bg-blue-100 dark:bg-blue-950",
    logoTextColor: "text-blue-600 dark:text-blue-400",
  },
  {
    id: "12",
    companyName: "GreenEnergy Co",
    contactName: "Chloe Blanc",
    contactRole: "Head of Sustainability",
    status: "Discovery",
    score: 48,
    value: 15000,
    logo: Building2,
    logoBgColor: "bg-teal-100 dark:bg-teal-950",
    logoTextColor: "text-teal-600 dark:text-teal-400",
  },
  {
    id: "13",
    companyName: "Fintech Express",
    contactName: "Hugo Mercier",
    contactRole: "CFO",
    status: "Qualified",
    score: 90,
    value: 110000,
    logo: Shield,
    logoBgColor: "bg-indigo-100 dark:bg-indigo-950",
    logoTextColor: "text-indigo-600 dark:text-indigo-400",
  },
  {
    id: "14",
    companyName: "CloudScale Inc",
    contactName: "Ines Dupont",
    contactRole: "DevOps Lead",
    status: "Negotiation",
    score: 67,
    value: 45000,
    logo: Cloud,
    logoBgColor: "bg-cyan-100 dark:bg-cyan-950",
    logoTextColor: "text-cyan-600 dark:text-cyan-400",
  },
  {
    id: "15",
    companyName: "Smart Mobility",
    contactName: "Antoine Fontaine",
    contactRole: "Fleet Manager",
    status: "Discovery",
    score: 58,
    value: 22000,
    logo: Rocket,
    logoBgColor: "bg-orange-100 dark:bg-orange-950",
    logoTextColor: "text-orange-600 dark:text-orange-400",
  },
  {
    id: "16",
    companyName: "Hyperion Commerce",
    contactName: "Manon Lambert",
    contactRole: "E-commerce Director",
    status: "High Priority",
    score: 87,
    value: 89000,
    logo: Building2,
    logoBgColor: "bg-violet-100 dark:bg-violet-950",
    logoTextColor: "text-violet-600 dark:text-violet-400",
  },
  {
    id: "17",
    companyName: "NextGen Software",
    contactName: "Arthur Girard",
    contactRole: "VP Sales",
    status: "Qualified",
    score: 74,
    value: 36000,
    logo: Cloud,
    logoBgColor: "bg-blue-100 dark:bg-blue-950",
    logoTextColor: "text-blue-600 dark:text-blue-400",
  },
  {
    id: "18",
    companyName: "BioHealth Group",
    contactName: "Lea Bonnet",
    contactRole: "Medical Director",
    status: "Negotiation",
    score: 93,
    value: 130000,
    logo: Shield,
    logoBgColor: "bg-emerald-100 dark:bg-emerald-950",
    logoTextColor: "text-emerald-600 dark:text-emerald-400",
  },
  {
    id: "19",
    companyName: "Urban Infra",
    contactName: "Louis Richard",
    contactRole: "Project Director",
    status: "Discovery",
    score: 62,
    value: 27000,
    logo: Building2,
    logoBgColor: "bg-zinc-100 dark:bg-zinc-800",
    logoTextColor: "text-zinc-800 dark:text-zinc-200",
  },
  {
    id: "20",
    companyName: "Vortex Gaming",
    contactName: "Mathilde Colin",
    contactRole: "Community Lead",
    status: "High Priority",
    score: 81,
    value: 49000,
    logo: Rocket,
    logoBgColor: "bg-fuchsia-100 dark:bg-fuchsia-950",
    logoTextColor: "text-fuchsia-600 dark:text-fuchsia-400",
  },
];
const Dashboard = () => {
  return (
    <div className="flex flex-col gap-6">
      <HeaderPropspect />
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
      <div className="flex w-full gap-4">
        <ChartProspect />
        <CampagneHealth />
      </div>
      <DesktopTable data={PropspectTableSeed} />
    </div>
  );
};

export const Route = createFileRoute("/")({
  component: Dashboard,
});
