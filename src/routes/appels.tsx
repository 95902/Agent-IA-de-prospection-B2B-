/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";
import Customer from "@/assets/customer.png";
import {
  Building2,
  Calendar,
  CircleX,
  List,
  MapPin,
  MicOff,
  NotebookPen,
  Paperclip,
  Pause,
  TrendingDown,
  TriangleAlert,
  User,
  UserX,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Textarea";
import { Card } from "@/components/ui/Card";
const CallCard = () => {
  return (
    <div className="rounded-lg group hover:bg-blue-100 transition-all duration-200 p-2 max-h-40 gap-4 w-full shrink-0 flex flex-col overflow-hidden">
      <div className="flex justify-between items-center text-nowrap">
        <div className="flex flex-col">
          <p className="text-lg group-hover:text-blue-700 font-bold">
            TechNova Solutions
          </p>
          <p className="text-sm">Régions cibles</p>
        </div>
        <div className="bg-white group-hover:bg-blue-100 rounded-lg px-2 p-1 border border-slate-200 group-hover:border-blue-300 w-fit group-hover:text-blue-700 transition-colors duration-200 dark:text-blue-400">
          En appel
        </div>
      </div>
      <div className="w-full flex-wrap gap-2 flex">
        <div className="bg-red-100 rounded-lg w-fit px-2 p-1 border border-red-300 text-red-700">
          SaaS
        </div>
        <div className="bg-red-100 rounded-lg w-fit px-2 p-1 border border-red-300 text-red-700">
          14 chefs
        </div>
        <div className="bg-red-100 rounded-lg w-fit px-2 p-1 border border-red-300 text-red-700">
          14 chefs
        </div>
        <div className="bg-red-100 rounded-lg w-fit px-2 p-1 border border-red-300 text-red-700">
          14 chefs
        </div>
        <div className="bg-red-100 rounded-lg w-fit px-2 p-1 border border-red-300 text-red-700">
          14 chefs
        </div>
        <div className="bg-red-100 rounded-lg w-fit px-2 p-1 border border-red-300 text-red-700">
          14 chefs
        </div>
        <div className="bg-red-100 rounded-lg w-fit px-2 p-1 border border-red-300 text-red-700">
          14 chefs
        </div>
        <div className="bg-red-100 rounded-lg w-fit px-2 p-1 border border-red-300 text-red-700">
          14 chefs
        </div>
      </div>
    </div>
  );
};

const Calls = () => {
  return (
    <div className="w-full lg:h-full flex flex-col lg:flex-row gap-4">
      <Card className="w-full lg:w-1/3 border rounded-lg h-full flex flex-col ">
        <div className="w-full rounded-t flex justify-between items-center bg-[#C6C6CD]/20 border-b-2 p-4">
          <p className="text-xl">FILE D'ATTENTE</p>
          <div className="bg-blue-100 rounded-lg px-2 p-1 border border-blue-300 text-blue-700">
            14 chefs
          </div>
        </div>
        <div className="w-full h-hull flex flex-col flex-1 p-4 gap-4 overflow-y-scroll">
          <CallCard />
          <CallCard />
          <CallCard />
          <CallCard />
          <CallCard />
          <CallCard />
          <CallCard />
        </div>
      </Card>
      <div className="w-full lg:w-1/3 border-2 overflow-hidden rounded-lg bg-transparent h-full flex flex-col p-6">
        <div className="flex flex-col gap-6">
          <div className="flex w-full justify-between items-center">
            <div className="h-full bg-gray-100 border-2 border-gray-300 rounded-lg w-fit object-cover">
              <img src={Customer} alt="call-customer" />
            </div>
            <div className="flex flex-col gap-1 items-end">
              <p className="text-lg">TechNova Solutions</p>
              <div className="px-2 py-1 bg-green-300  w-fit rounded-3xl">
                <p className="text-black text-sm">Auto-Enrichissement Actif</p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 items-center gap-2 w-full">
            <div className="flex gap-2 items-center shrink-0 overflow-hidden">
              <User />
              <p className="text-lg text-nowrap">Marc Dupont (CEO)</p>
            </div>
            <div className="flex gap-2 items-center">
              <MapPin />
              <p className="text-lg text-nowrap">Paris, France</p>
            </div>
            <div className="flex gap-2 items-center">
              <Building2 />
              <p className="text-lg text-nowrap">technova.io</p>
            </div>
          </div>
          <div className="flex flex-col gap-4">
            <p>POINTS DE FRICTION</p>
            <div className="w-full flex flex-col gap-4 rounded-lg border border-red-300 bg-red-100 p-4">
              <div className="flex gap-2 items-center shrink-0">
                <TriangleAlert className="text-red-700" size={25} />
                <p className="text-lg text-red-700 font-bold">
                  Fin du contrat actuel
                </p>
              </div>
              <p className="text-muted-foreground text-xs">
                Le contrat actuel expire dans 45 jours. Période critique pour
                son remplacement.
              </p>
            </div>
            <div className="w-full flex flex-col gap-4 rounded-lg border border-blue-300 bg-blue-100 p-4">
              <div className="flex gap-2 items-center shrink-0">
                <TrendingDown className="text-blue-700" size={25} />
                <p className="text-lg text-blue-700 font-bold">
                  Fin du contrat actuel
                </p>
              </div>
              <p className="text-muted-foreground text-xs">
                Le contrat actuel expire dans 45 jours. Période critique pour
                son remplacement.
              </p>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <p>DERNIERE INTERACTION</p>
            <div className="w-full flex flex-col gap-4 pl-4">
              <p>
                <span className="font-bold">Courriel non sollicité ouvert</span>{" "}
                · il y a 2 heures Objet : « Développement de l’infrastructure de
                TechNova »
              </p>
              <p>
                <span className="font-bold">Courriel non sollicité ouvert</span>{" "}
                · il y a 2 heures Objet : « Développement de l’infrastructure de
                TechNova »
              </p>
            </div>
          </div>
          <div className="flex h-full flex-col gap-4">
            <p>LOCALISATION</p>
            <div className="w-full flex border-2 flex-col bg-gray-300 border-gray-500 rounded-xl flex-1"></div>
          </div>
        </div>
      </div>
      <div className="w-full lg:w-1/3 flex flex-col gap-4 h-full overflow-hidden rounded-lg">
        <Card className="w-full shrink-0 border gap-2 border-gray-400 items-center rounded-lg flex flex-col p-4">
          <div className="px-2 py-1 rounded-xl w-fit bg-blue-600 border border-blue-800">
            <p className="text-sm text-white">20:38</p>
          </div>
          <p className="font-bold">+33 1 70 23 4X XX</p>
          <p>Connecting via VoIP-01</p>
          <div className="flex w-full gap-4 items-center">
            <Button className="flex-1 rounded-lg flex-col border border-gray-500 flex items-center justify-center h-20 bg-white">
              <MicOff className="text-blue-700" size={20} />
              <p className="text-blue-700 text-sm">Mute</p>
            </Button>
            <Button className="flex-1 rounded-lg flex-col border border-gray-500 flex items-center justify-center h-20 bg-white">
              <Pause className="text-blue-700" size={20} />
              <p className="text-blue-700 text-sm">Hold</p>
            </Button>
          </div>
          <div className="w-full rounded-lg flex gap-2 items-center justify-center h-20 bg-black">
            <Calendar className="text-green-700" />
            <p className="text-green-700">RDV (Ensemble de réunion)</p>
          </div>
          <div className="flex w-full gap-4 items-center">
            <Button className="flex-1 rounded-lg gap-2 border border-red-500 flex items-center justify-center h-20 bg-red-100">
              <CircleX className="text-red-700" size={20} />
              <p className="text-red-700 text-sm">Refus</p>
            </Button>
            <Button className="flex-1 rounded-lg gap-2 border border-gray-500 flex items-center justify-center h-20 bg-gray-100">
              <UserX className="text-blue-700" size={20} />
              <p className="text-blue-700 text-sm">Absent</p>
            </Button>
          </div>
          <Button className="w-full rounded-lg border-gray-500 bg-gray-200 flex items-center justify-center">
            <p className="text-black">Autre résultat</p>
          </Button>
        </Card>
        <Card className="w-full flex-1 border rounded-lg flex flex-col">
          <div className="w-full h-fit flex items-center justify-between p-4">
            <p>NOTES EN DIRECT</p> <NotebookPen />
          </div>
          <Textarea
            className="flex-1 border-y rounded-none"
            placeholder="Type call notes here... Mention objections, budget, or timeline."
          />
          <div className="w-full itms-center flex gap-4 justify-between p-4">
            <div className="flex items-center gap-4">
              <List /> <Paperclip />
            </div>
            <Button>Sauvegarder une note</Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/appels")({
  component: Calls,
});
