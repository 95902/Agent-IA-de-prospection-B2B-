/* eslint-disable react-refresh/only-export-components */
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Progress } from "@/components/ui/Progress";
import { createFileRoute } from "@tanstack/react-router";
import {
  Building2,
  Calendar,
  Eye,
  Mail,
  MapPin,
  MessageSquare,
  MousePointerClick,
  PencilLine,
  Phone,
  Play,
  Star,
  User,
} from "lucide-react";

const PropspectId = () => {
  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between mb-4">
        <div className="flex flex-col space-y-1">
          <CardTitle className="font-bold text-2xl">Alexander Vance</CardTitle>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="rounded-lg">
            <Phone /> Appeler
          </Button>
          <Button variant="outline" className="rounded-lg">
            <Calendar /> Email
          </Button>
          <Button className="rounded-lg">
            <MessageSquare /> Message
          </Button>
        </div>
      </div>
      <div className="flex-1 flex flex-col lg:flex-row gap-4">
        <div className="flex-1 lg:w-1/3 flex flex-col gap-4">
          <Card className="min-h-fit overflow-auto  w-full border flex flex-col gap-4 border-gray-400 rounded-lg p-8">
            <div className="flex gap-2 items-center">
              <User size={70} />
              <div className="flex flex-col">
                <p className="font-bold text-lg">Alexander Vance</p>
                <p className="text-muted-foreground text-xs">
                  VP of Engineering at CloudScale AI
                </p>
              </div>
            </div>
            <div className="flex flex-col gap-4 ">
              <div className="flex items-center gap-4">
                <Mail className="text-blue-700" />
                <p>a.vance@cloudscale.ai</p>
              </div>
              <div className="flex items-center gap-4">
                <Phone className="text-blue-700" />
                <p>+1 (555) 012-9842</p>
              </div>
              <div className="flex items-center gap-4">
                <MapPin className="text-blue-700" />
                <p>San Francisco, CA</p>
              </div>
              <div className="flex items-center gap-4">
                <Building2 className="text-blue-700" />
                <p>Series D • 450-500 employés</p>
              </div>
            </div>
            <div className="min-h-0 w-full border" />
            <div className="flex justify-between items-center gap-4 h-full">
              <div className="rounded-sm bg-gray-200 flex-1 h-full flex items-center text-center justify-center">
                Technologie
              </div>
              <div className="rounded-sm bg-gray-200 flex-1 h-full flex items-center text-center justify-center">
                Prise de décision
              </div>
              <div className="rounded-sm bg-gray-200 flex-1 h-full flex items-center text-center justify-center">
                Adopteur précoce
              </div>
            </div>
          </Card>

          <div className=" gap-4 w-full bg-black flex flex-col rounded-lg p-4 dark:border-white dark:border">
            <div className="flex justify-between items-center">
              <p className="text-xl font-bold text-white">
                Score global des prospects
              </p>
              <div className="bg-blue-500 rounded-lg px-4 py-2">
                <p className="text-white text-nowrap font-bold">analyse IA</p>
              </div>
            </div>

            <div className="flex flex-col items-center gap-4 w-full">
              <p className="text-3xl font-bold w-full text-start text-white ">
                92 / 100
              </p>
              <Progress
                value={92}
                className="w-full shrink-0"
                indicatorClassName="bg-green-500"
              />
            </div>
            <p className="text-purple-200 flex-1">
              « Signal fort détecté via les récents rapports d'expansion de
              l'infrastructure cloud et un intérêt secondaire suite aux annonces
              de financement de série D. Vance correspond parfaitement au profil
              de la "tech à forte croissance". »
            </p>
            <div className="flex items-center gap-2 p-4 w-full">
              <Star className="text-white" size={30} />
              <p className="text-white font-semibold">CONFIDENCE: 98%</p>
            </div>
          </div>
        </div>

        <div className="lg:w-2/3 h-full flex flex-col gap-4 rounded-lg">
          <Card className=" flex-1 border rounded-lg flex flex-col border-gray-400  gap-0">
            <div className="w-full rounded-t-lg flex flex-col lg:flex-row justify-between lg:items-center border-b-2 p-4 bg-[#C6C6CD]/20">
              <p className="text-gray-700 text-lg dark:text-white text-nowrap">
                Logique de notation de l'IA
              </p>
              <p className="text-blue-500">Afficher les poids détaillés</p>
            </div>
            <div className="flex-1 flex flex-col lg:flex-row p-6 gap-6">
              <div className="w-full lg:w-1/2 h-full flex justify-between flex-col gap-4">
                <div className="w-full justify-between flex flex-col lg:flex-row lg:items-center gap-1">
                  <p className="font-bold">Analyse sémantique LLM</p>
                  <p className="text-green-500 text-nowrap">+45 pts</p>
                </div>
                <p className="text-muted-foreground flex-1 overflow-hidden">
                  Une correspondance a été trouvée entre une publication récente
                  du prospect sur LinkedIn concernant la « rareté des GPU » et
                  l'argument de vente unique de notre produit en matière
                  d'optimisation de l'infrastructure.
                </p>
                <Progress
                  value={25}
                  className="w-full shrink-0"
                  indicatorClassName="bg-green-500"
                />
              </div>
              <div className="w-full lg:w-1/2 h-full flex justify-between flex-col gap-4">
                <div className="w-full justify-between flex flex-col lg:flex-row lg:items-center gap-1">
                  <p className="font-bold">Score de match intégré</p>
                  <p className="text-green-500 text-nowrap">+32 pts</p>
                </div>
                <p className="text-muted-foreground flex-1 overflow-hidden">
                  Vector similarity of 0.89 with 'Champion' segment. High
                  correlation with previous high-conversion profiles in the
                  AI/ML vertical.
                </p>
                <Progress
                  value={32}
                  className="w-full shrink-0"
                  indicatorClassName="bg-green-500"
                />
              </div>
            </div>
          </Card>
          <Card className="border flex-col flex rounded-lg border-gray-400  gap-0">
            <div className="w-full flex flex-col lg:flex-row justify-between rounded-t-lg lg:items-center p-4 bg-[#C6C6CD]/20">
              <p className="text-gray-700 text-lg dark:text-white">
                Historique des interactions
              </p>
              <div className="flex items-center gap-2">
                <Button variant="ghost" className="rounded-lg">
                  Toutes les activités
                </Button>
                <Button variant="ghost" className="rounded-lg">
                  Communications
                </Button>
              </div>
            </div>

            <div className="flex flex-col gap-8 p-4 overflow-scroll">
              <div className="flex flex-col gap-2 w-full">
                <div className="w-full justify-between flex items-center">
                  <p className="font-bold text-lg">Analyse sémantique LLM</p>
                  <p className="text-muted-foreground text-sm">
                    Oct 24, 2023 • 10:15 AM
                  </p>
                </div>
                <div className="border rounded-lg flex flex-col p-4 w-full gap-2">
                  <p className="italic">
                    "Subject: Solving the GPU scale problem for CloudScale
                    AI..."
                  </p>
                  <div className="flex items-center gap-8">
                    <div className="flex items-center gap-2">
                      <Eye className="text-green-500" size={20} />
                      <p className="text-green-500 text-sm">Ouvert 3x</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <MousePointerClick className="text-green-500" size={20} />
                      <p className="text-green-500 text-sm">Lien cliqué</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-2 w-full">
                <div className="w-full justify-between flex items-center">
                  <p className="font-bold text-lg">
                    Visite du site web - Page des tarifs
                  </p>
                  <p className="text-muted-foreground text-sm">
                    Oct 25, 2023 • 02:30 PM
                  </p>
                </div>
                <p className="text-muted-foreground">
                  IP identified as CloudScale AI Corp. Duration: 4m 12s.
                </p>
              </div>

              <div className="flex flex-col gap-2 w-full">
                <div className="w-full justify-between flex items-center">
                  <p className=" text-xl text-muted-foreground">
                    Upcoming: Technical Demo
                  </p>
                  <p className="text-muted-foreground text-sm">
                    Nov 02, 2023 • 10:00 AM
                  </p>
                </div>
                <p>
                  Planifié via Calendly. Participants : A. Vance, S. Chen
                  (architecte).
                </p>
              </div>
            </div>

            <div className="w-full flex justify-between rounded-lg rounded-t-none items-center p-4">
              <div className="flex w-full items-center gap-4">
                <PencilLine />
                <Input
                  type="search"
                  placeholder="Search..."
                  className="flex-1"
                />
                <Button variant="ghost">
                  <Play />
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/prospects/$prospectId")({
  component: PropspectId,
});
