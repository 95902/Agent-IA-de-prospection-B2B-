import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";

interface Campaign {
  title: string;
  status: "Active" | "Paused" | "Draft" | "Completed";
  completionPercentage: number;
  leadsCount: number;
}

const campaignsSeed: Campaign[] = [
  {
    title: "Tech Giants Outreach",
    status: "Active",
    completionPercentage: 72,
    leadsCount: 128,
  },
  {
    title: "SaaS Q4 Blitz",
    status: "Paused",
    completionPercentage: 45,
    leadsCount: 84,
  },
  {
    title: "Startup Seed Hunt",
    status: "Active",
    completionPercentage: 91,
    leadsCount: 312,
  },
];

const getProgressColor = (status: Campaign["status"]) => {
  switch (status) {
    case "Active":
      return "bg-emerald-600";
    case "Paused":
      return "bg-blue-600";
    default:
      return "bg-blue-600";
  }
};

const getBadgeStyle = (status: Campaign["status"]) => {
  switch (status) {
    case "Active":
      return "bg-emerald-50 text-emerald-800 hover:bg-emerald-50 border-emerald-200/60";
    case "Paused":
      return "bg-blue-50 text-blue-800 hover:bg-blue-50 border-blue-200/60";
    default:
      return "bg-slate-100 text-slate-800";
  }
};

const HealthCard = ({ campaign }: { campaign: Campaign }) => {
  return (
    <div
      className={`p-4 border cursor-pointer flex flex-col hover:bg-[#C6C6CD]/30 gap-4 rounded-lg bg-[#C6C6CD]/10 `}
    >
      <div className="flex items-center justify-between">
        <div className="flex flex-col  gap-2">
          <h3 className="text-lg font-semibold">{campaign.title}</h3>
        </div>
        <Badge variant="outline" className={getBadgeStyle(campaign.status)}>
          {campaign.status}
        </Badge>
      </div>
      <Progress
        value={campaign.completionPercentage}
        className="w-full shrink-0"
        indicatorClassName={getProgressColor(campaign.status)}
      />
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          {campaign.completionPercentage}% complete
        </p>
        <p className="text-sm text-muted-foreground">
          {campaign.leadsCount} Leads
        </p>
      </div>
    </div>
  );
};

export const CampagneHealth = () => {
  return (
    <div className="flex flex-col gap-4 p-6 bg-white border rounded-lg">
      <h2 className="text-black font-bold">Campagnes</h2>
      {campaignsSeed.map((campaign) => (
        <HealthCard key={campaign.title} campaign={campaign} />
      ))}
    </div>
  );
};
