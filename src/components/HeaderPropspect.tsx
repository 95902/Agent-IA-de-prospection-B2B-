import { Calendar, Download } from "lucide-react";
import { Button } from "./ui/Button";
import { CardDescription, CardTitle } from "./ui/Card";

export const HeaderPropspect = () => {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex flex-col space-y-1">
        <CardTitle>Aperçu de la direction</CardTitle>
        <CardDescription>
          Informations en temps réel sur le pipeline et la vitesse des
          campagnes.
        </CardDescription>
      </div>
      <div className="flex items-center  gap-2">
        <Button variant="outline" className="rounded-lg">
          {" "}
          <Calendar /> Les 30 derniers jours
        </Button>
        <Button className="rounded-lg">
          <Download /> Exporter le report
        </Button>
      </div>
    </div>
  );
};
