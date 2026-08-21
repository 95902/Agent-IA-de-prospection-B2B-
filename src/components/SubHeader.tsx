import { Calendar, Download } from "lucide-react";
import { Button } from "./ui/Button";
import { CardDescription, CardTitle } from "./ui/Card";

interface SubHeaderProps {
  title: string;
  description: string;
}
export const SubHeader = ({ title, description }: SubHeaderProps) => {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex flex-col space-y-1">
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </div>
      <div className="flex items-center  gap-2">
        <Button variant="outline" className="rounded-lg">
          <Calendar /> Les 30 derniers jours
        </Button>
        <Button disabled title="À venir" className="rounded-lg">
          <Download /> Exporter le report
        </Button>
      </div>
    </div>
  );
};
