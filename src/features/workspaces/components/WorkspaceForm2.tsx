import { Field, FieldDescription, FieldLabel } from "@/components/ui/Field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import { useState, type SubmitEvent, type MouseEvent } from "react";
import { Input } from "@/components/ui/Input";
import { Progress } from "@/components/ui/Progress";
import type { BaseUIEvent } from "@base-ui/react/types";
import { Card } from "@/components/ui/Card";
import type { StepsProps } from "../types";
import { DEPARTEMENTS } from "../seed";
import { WorkspaceWrapper } from "./WorkspaceWrapper";

export const WorkspaceForm2 = ({ onNext, onPrevious }: StepsProps) => {
  const [numberEmploye, setNumberEmploye] = useState<string | null>(null);
  const [audience] = useState<number>(25);

  const handleReset = () => {
    setNumberEmploye(null);
  };

  const handleNext = (e: SubmitEvent) => {
    e.preventDefault();
    onNext();
  };

  const handlePrevious = (e: BaseUIEvent<MouseEvent<HTMLButtonElement>>) => {
    e.preventDefault();
    onPrevious?.();
  };

  return (
    <WorkspaceWrapper
      handleNext={handleNext}
      handleReset={handleReset}
      handlePrevious={handlePrevious}
      onNext={onNext}
      title="Cible"
      description="Filtrez vos prospects selon la cible choisie"
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 content-start w-full">
        <Field>
          <FieldLabel>Nom du client</FieldLabel>
          <Input
            id="input-client-name"
            type="text"
            placeholder="E. G. Acme Corp"
          />
          <FieldDescription className="text-muted-foreground text-xs">
            Saisissez un ou plusieurs domaines professionnels.
          </FieldDescription>
        </Field>
        <Field>
          <FieldLabel>Codes NAF / SIC</FieldLabel>
          <Input
            id="input-principal-client-name"
            type="text"
            placeholder="e. g. 6201Z, 7022Z"
          />
          <FieldDescription className="text-muted-foreground text-xs">
            Saisissez les codes d'activité séparés par des virgules.
          </FieldDescription>
        </Field>
        <Field>
          <FieldLabel htmlFor="select-naf">Nombre d'employés</FieldLabel>
          <Select
            value={numberEmploye}
            onValueChange={(val) => setNumberEmploye(val)}
          >
            <SelectTrigger id="select-industry">
              <SelectValue placeholder="Sélectionnez un secteur ou une industrie" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                {DEPARTEMENTS.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </Field>
        <Card className="p-4 shrink-0 rounded-lg border-2  flex flex-col overflow-hidden">
          <p className="text-blue-500 font-bold">Cible</p>
          <div className="flex flex-col items-center gap-2 w-full">
            <div className="flex justify-between items-center gap-1 w-full">
              <p className="text-lg ">Audience estimé</p>
              <span className="font-bold text-right text-2xl">1240</span>
            </div>
            <Progress
              value={audience}
              className="w-full shrink-0"
              indicatorClassName="bg-green-500"
            />
            <p className="text-xs text-muted-foreground">
              Vos filtres actuels correspondent à 65 % du pool total disponible
              dans cette région.
            </p>
          </div>
        </Card>
      </div>
    </WorkspaceWrapper>
  );
};
