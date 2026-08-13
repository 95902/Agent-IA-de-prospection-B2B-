import type { StepsProps } from "../types";
import { Button } from "@/components/ui/Button";
import { type MouseEvent } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CircleMinus,
  Flame,
  Mail,
  Settings,
  UserSearch,
} from "lucide-react";
import { Progress } from "@/components/ui/Progress";
import type { BaseUIEvent } from "@base-ui/react/types";
import Tower from "@/assets/tower.png";
import { Switch } from "@/components/ui/Switch";
import { Card } from "@/components/ui/Card";

export const WorkspaceForm4 = ({ onPrevious }: StepsProps) => {
  // const handleNext = (e: SubmitEvent) => {
  //   e.preventDefault();
  //   onNext();
  // };

  const handlePrevious = (e: BaseUIEvent<MouseEvent<HTMLButtonElement>>) => {
    e.preventDefault();
    onPrevious?.();
  };

  return (
    <div className="w-full h-full flex flex-col gap-4">
      <div className="flex flex-col">
        <p className="text-3xl font-bold">Récapitulatif final </p>
        <p className="text-sm w-4/5">
          Vérifiez les détails avant de lancer la création du nouveau profil
          client.
        </p>
      </div>
      <div className="flex flex-1 flex-col w-full min-h-0 gap-4">
        <div className="flex h-2/5 w-full gap-4">
          <Card className="px-8 py-6 w-1/3 rounded-lg border-2 min-w-md gap-6 flex flex-col overflow-hidden">
            <div className="flex gap-2 items-center ">
              <UserSearch className="text-blue-700" size={30} />
              <p className="text-blue-700 text-xl ">IDENTITÉ CLIENT</p>
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex flex-col">
                <p className="text-sm">Nom de l'entreprise</p>
                <p className="text-xl font-bold">Acme Corp Solutions</p>
              </div>
              <div className="flex flex-col">
                <p className="text-sm">Secteur d'activité</p>
                <p className="text-lg">Technologie & SaaS</p>
              </div>
              <div className="flex flex-col">
                <p className="text-sm">Site Web</p>
                <a className="text-lg">www.acme-solutions.io</a>
              </div>
            </div>
          </Card>
          <Card className="px-8 py-6 w-2/3 rounded-lg border-2 min-w-md gap-6 flex flex-col overflow-hidden">
            <div className="flex justify-between w-full items-center">
              <div className="flex gap-2 items-center">
                <UserSearch className="text-blue-700" size={30} />
                <p className="text-blue-700 text-xl">PARAMÈTRES DE CIBLAGE</p>
              </div>
              <Button variant="outline" className="flex gap-2 items-center">
                Modifier
              </Button>
            </div>
            <div className="grid grid-cols-2 w-full h-full">
              <div className="flex flex-col">
                <p className="text-sm">Régions cibles</p>
                <p className="text-lg">Europe de l'Ouest / Amérique du Nord</p>
              </div>
              <div className="flex flex-col">
                <p className="text-sm">Technologies utilisées</p>
                <p className="text-lg">Salesforce / Segment / Hubspot</p>
              </div>
              <div className="flex flex-col">
                <p className="text-sm">Effectifs visés</p>
                <p className="text-lg">50 - 500 employés (Scale-ups)</p>
              </div>
              <div className="flex flex-col">
                <p className="text-sm">Budget estimé</p>
                <p className="text-lg">15k€ - 50k€ / an</p>
              </div>
            </div>
          </Card>
        </div>
        <Card className="p-8 h-1.5/5 w-full rounded-lg border-2 min-w-md gap-4 flex flex-col overflow-hidden">
          <div className="flex gap-2 items-center">
            <Flame className="text-blue-700" size={30} />
            <p className="text-blue-700 text-xl">
              PROFIL DE L'IDEAL CUSTOMER (ICP)
            </p>
          </div>
          <div className="flex-1 min-w-md flex justify-between gap-4">
            <Card className="w-full h-full gap-1 flex-col px-4 py-2 justify-between flex rounded-lg border overflow-hidden">
              <p className="text-gray-700">Persona Clé</p>
              <p className="text-lg font-bold">
                Directeur Commercial / VP Sales
              </p>
              <p className="text-muted-foreground text-sm">
                Décideur principal avec pouvoir de signature sur les outils de
                prospection.
              </p>
            </Card>
            <Card className="w-full h-full flex-col gap-2 px-4 py-2 justify-between flex rounded-lg border overflow-hidden">
              <p className="text-gray-700">Points de Douleur</p>
              <div className="w-full h-full gap-1 pl-2 flex flex-col">
                <div className="flex items-center gap-2">
                  <CircleMinus size={17} className="text-red-600" />
                  <p className="text-sm">Manque de données fraîches</p>
                </div>
                <div className="flex items-center gap-2">
                  <CircleMinus size={17} className="text-red-600" />
                  <p className="text-sm">Cycles de vente trop longs</p>
                </div>
              </div>
            </Card>
            <Card className="w-full h-full flex-col px-4 py-2 gap-2 flex  rounded-lg border overflow-hidden">
              <p className="text-gray-700">Indice de Qualité</p>
              <div className="flex items-center gap-4 w-full pr-4">
                <Progress
                  value={50}
                  className="flex-1 shrink-0"
                  indicatorClassName="bg-blue-500"
                />
                <span className="font-bold  text-sm w-10 text-right text-blue-500">
                  50 %
                </span>
              </div>
              <p className="text-sm">
                Forte correspondance avec l'historique de conversion.
              </p>
            </Card>
          </div>
        </Card>
        <div className="flex h-1.5/5 w-full gap-4">
          <Card className="py-4 px-8 w-1/2 rounded-lg border-2 min-w-md  flex flex-col overflow-hidden">
            <div className="flex gap-2 items-center ">
              <Settings className="text-gray-700" size={30} />
              <p className="text-gray-700 text-xl ">ALERTES & AUTOMATISATION</p>
            </div>
            <div className="flex gap-8 items-center h-full">
              <Mail className="text-blue-700" size={30} />
              <div className="flex flex-col flex-1">
                <p className="text-lg font-bold">
                  Rapport de prospection hebdomadaire
                </p>
                <p className="text-muted-foreground text-sm">
                  Activé pour contact@acme.io
                </p>
              </div>
              <Switch />
            </div>
          </Card>
          <Card className="p-8 w-1/2 rounded-lg border-2 min-w-md gap-8 flex flex-row overflow-hidden">
            <div className="rounded-lg h-full overflow-hidden max-h-20 max-w-20">
              <img
                src={Tower}
                alt="image-tower"
                className="h-full w-full object-cover"
              />
            </div>
            <div className="flex flex-col justify-between">
              <div className="flex flex-col gap-1">
                <p className="text-xl font-extrabold">Identité Visuelle</p>
                <p className="text-muted-foreground pb-4">
                  Le logo et les images de l'entreprise seront automatiquement
                  récupérés via Clearbit.
                </p>
              </div>
              <div className="px-2 py-1 bg-green-300 w-fit rounded-3xl">
                <p className="text-black text-sm">Auto-Enrichissement Actif</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
      <div className="flex w-full justify-between items-center">
        <Button
          type="button"
          className="w-fit"
          onClick={(e) => handlePrevious(e)}
        >
          <ArrowLeft /> Retour
        </Button>
        <Button type="submit" className="w-fit">
          Suivant <ArrowRight />
        </Button>
      </div>
    </div>
  );
};
