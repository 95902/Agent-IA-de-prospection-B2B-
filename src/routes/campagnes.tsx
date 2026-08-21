/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";
import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
import { Card } from "@/components/ui/Card";
import { CampaignForm } from "@/features/campaigns/components/CampaignForm";
import { BREADCRUMBS } from "@/features/campaigns/seed";
import { Info } from "lucide-react";

const Campaigns = () => (
  <div className="w-full h-full flex flex-col lg:flex-row gap-4 overflow-y-scroll">
    <div className="flex flex-col gap-6 flex-1">
      <h1 className="text-2xl font-bold">Création de campagne</h1>
      <h2 className="text-sm text-muted-foreground">
        Configurez vos paramètres de ciblage et de prospection pour commencer à
        trouver des prospects qualifiés.
      </h2>
      <Breadcrumbs data={BREADCRUMBS} step={0} />
      <CampaignForm />
    </div>
    <div className="flex flex-col gap-4 md:max-w-full lg:max-w-md">
      <Card className="w-full border rounded-xl p-8 flex flex-col gap-3">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Info />
          <p className="font-semibold">Estimations</p>
        </div>
        <p className="text-sm text-muted-foreground">
          Les estimations en direct (volume de prospects, précision du profil)
          seront calculées une fois la création de campagne câblée à l'API
          d'écriture. Pour l'instant, ce formulaire n'enregistre pas encore.
        </p>
      </Card>
    </div>
  </div>
);

export const Route = createFileRoute("/campagnes")({
  component: Campaigns,
});
