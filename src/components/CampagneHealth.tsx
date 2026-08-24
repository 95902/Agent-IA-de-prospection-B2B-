import { useQuery } from "@tanstack/react-query";
import { getCampagnes, type Campagne } from "@/lib/api";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";
import { Card } from "./ui/Card";
import { Progress } from "./ui/Progress";

const badgeStyle = (statut: string) => {
  switch (statut) {
    case "active":
    case "en_cours":
      return "bg-emerald-50 text-emerald-800 hover:bg-emerald-50 border-emerald-200/60";
    case "terminee":
      return "bg-blue-50 text-blue-800 hover:bg-blue-50 border-blue-200/60";
    default: // brouillon, pause…
      return "bg-slate-100 text-slate-800 hover:bg-slate-100 border-slate-200/60";
  }
};

const barColor = (statut: string) =>
  statut === "active" || statut === "en_cours"
    ? "bg-emerald-600"
    : "bg-slate-500";

const HealthCard = ({
  campagne,
  maxQualifies,
}: {
  campagne: Campagne;
  maxQualifies: number;
}) => {
  // Barre relative : part des qualifiés de cette campagne vs la meilleure.
  const value = maxQualifies > 0
    ? Math.round((campagne.prospects_qualifies / maxQualifies) * 100)
    : 0;
  return (
    <Card className="p-4 border cursor-pointer flex flex-col gap-4 rounded-lg">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-lg font-semibold">{campagne.nom}</h3>
        <Badge variant="outline" className={badgeStyle(campagne.statut)}>
          {campagne.statut}
        </Badge>
      </div>
      <Progress
        value={value}
        className="w-full shrink-0"
        indicatorClassName={barColor(campagne.statut)}
      />
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          {campagne.prospects_collectes} collectés
        </p>
        <p className="text-sm text-muted-foreground">
          {campagne.prospects_qualifies} qualifiés
        </p>
      </div>
    </Card>
  );
};

export const CampagneHealth = () => {
  const { data: campagnes, isLoading } = useQuery({
    queryKey: ["campagnes"],
    queryFn: getCampagnes,
  });

  const maxQualifies = Math.max(
    1,
    ...(campagnes ?? []).map((c) => c.prospects_qualifies),
  );

  return (
    <Card className="min-w-56 flex flex-col gap-4 p-6 border rounded-lg">
      <h2 className="text-black font-bold dark:text-white">Campagnes</h2>
      {isLoading && (
        <p className="text-sm text-muted-foreground">Chargement…</p>
      )}
      {campagnes?.length === 0 && (
        <p className="text-sm text-muted-foreground">Aucune campagne.</p>
      )}
      {campagnes?.map((campagne) => (
        <HealthCard
          key={campagne.id}
          campagne={campagne}
          maxQualifies={maxQualifies}
        />
      ))}
      <Button
        variant="outline"
        className="w-full rounded-lg border-[#0051D5]/20"
      >
        <span className="text-[#0051D5]"> Voir toutes les campagnes</span>
      </Button>
    </Card>
  );
};
