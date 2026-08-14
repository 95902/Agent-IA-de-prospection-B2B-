/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";
import { Progress } from "@/components/ui/Progress";
import { CircleAlert, CircleCheck, TrendingUp } from "lucide-react";
import image from "@/assets/Image.png";
import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
import { Card } from "@/components/ui/Card";
import { CampaignForm } from "@/features/campaigns/components/CampaignForm";

const BREADCRUMBS = ["INFORMATIONS", "CIBLE", "MOTS CLEF"];

const VERIFICATIONS = [
  "Email vérifié",
  "Téléphone valide",
  "Profil LinkedIn lié",
];

const Campaigns = () => {

  return (
    <div className="w-full h-full flex flex-col lg:flex-row gap-4 overflow-y-scroll">
      <div className="flex flex-col gap-6 flex-1">
        <h1 className="text-2xl font-bold">Création de campagne</h1>
        <h2 className="text-sm text-muted-foreground">
          Configurez vos paramètres de ciblage et de prospection pour commencer
          à trouver des prospects qualifiés.
        </h2>
        <Breadcrumbs data={BREADCRUMBS} step={0} />
        <CampaignForm />
      </div>
      <div className="flex flex-col gap-4 md:max-w-full lg:max-w-md">
        <Card className="w-full border overflow-hidden rounded-xl">
          <div className="flex flex-col gap-4 border-b rounded-t-lg px-8 py-6 bg-muted/40">
            <p>Estimations en direct</p>
            <p>
              <span className="font-bold text-5xl  text-blue-700">2482 </span>
              Prospects
            </p>
          </div>
          <div className="flex flex-col gap-6 px-8  w-full">
            <div className="flex flex-col items-center gap-2 w-full">
              <div className="flex justify-between items-center gap-1 w-full">
                <p className="text-xs font-bold">Précision du profil</p>
                <span className="font-bold w-6 text-right text-xs text-green-500">
                  25 %
                </span>
              </div>
              <Progress
                value={25}
                className="w-full shrink-0"
                indicatorClassName="bg-green-500"
              />
            </div>
            <div className="flex flex-col items-center gap-2 w-full">
              {VERIFICATIONS.map((text, index) => (
                <div key={index} className="flex items-center gap-2 w-full">
                  <CircleCheck className="text-green-500 shrink-0" />
                  <p>{text}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="flex gap-2 items-center p-8 pt-0 ">
            <CircleAlert />
            <p className="text-sm text-muted-foreground">
              Données mises à jour il y a 2 minutes
            </p>
          </div>
        </Card>
        <Card className="flex-1 flex flex-col w-full border-2 gap-6 overflow-hidden rounded-lg p-8 shrink-0 bg-muted/40">
          <div className="flex items-center gap-2">
            <TrendingUp />
            <p>Estimations en direct</p>
          </div>
          <div className="w-full h-auto">
            <img src={image} alt="Description" className="object-cover" />
          </div>
          <p className="text-sm text-muted-foreground text-wrap">
            Les entreprises SaaS de votre région sélectionnée constatent
            actuellement une augmentation de 15 % des embauches pour les postes
            d'ingénierie.
          </p>
        </Card>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/campagnes")({
  component: Campaigns,
});
