/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/ui/Card";
import { CampaignForm } from "@/features/campaigns/components/CampaignForm";
import { Info } from "lucide-react";

const Campaigns = () => (
  <div className="w-full h-full flex flex-col lg:flex-row gap-4 overflow-y-scroll">
    <div className="flex flex-col gap-6 flex-1">
      <h1 className="text-2xl font-bold">Création de campagne</h1>
      <h2 className="text-sm text-muted-foreground">
        Définissez le profil client idéal (ICP) : cible sectorielle, zone,
        effectif et mots-clés. La campagne est créée en brouillon.
      </h2>
      <CampaignForm />
    </div>
    <div className="flex flex-col gap-4 md:max-w-full lg:max-w-md">
      <Card className="w-full border rounded-xl p-8 flex flex-col gap-3">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Info />
          <p className="font-semibold">Création = configuration seulement</p>
        </div>
        <p className="text-sm text-muted-foreground">
          Valider crée la campagne en <b>brouillon</b> (client + critères + ICP) —
          aucun appel API, aucun prospect collecté. Le <b>lancement du pipeline</b>{" "}
          (INSEE / Tavily / Claude) est une action séparée et explicite, pour
          maîtriser les crédits.
        </p>
      </Card>
    </div>
  </div>
);

export const Route = createFileRoute("/campagnes")({
  component: Campaigns,
});
