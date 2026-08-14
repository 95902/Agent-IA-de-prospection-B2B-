import { Field, FieldLabel } from "@/components/ui/Field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import { useState, type SubmitEvent } from "react";
import { Input } from "@/components/ui/Input";
import type { StepsProps } from "../types";
import { DEPARTEMENTS } from "../seed";
import { WorkspaceWrapper } from "./WorkspaceWrapper";

export const WorkspaceForm1 = ({ onNext }: StepsProps) => {
  const [departement, setDepartement] = useState<string | null>(null);

  const handleReset = () => {
    setDepartement(null);
  };

  const handleNext = (e: SubmitEvent) => {
    e.preventDefault();
    onNext();
  };

  //   const form = useForm({
  //     defaultValues: {
  //       campaignNumber: "",
  //       objective: "",
  //       level: "",
  //     },
  //     validators: {
  //       onSubmit: WorkspaceForm1Schema,
  //     },
  //     onSubmit: async ({ value }) => {
  //       console.log("Données du formulaire soumises :", value);
  //       // Traitement de l'étape suivante ici
  //     },
  //   });

  return (
    <WorkspaceWrapper
      handleNext={handleNext}
      handleReset={handleReset}
      onNext={onNext}
      title="Information du client"
      description="Filtrez vos prospects selon les différents critères"
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 content-start w-full">
        <Field>
          <FieldLabel>Nom du client</FieldLabel>
          <Input
            id="input-client-name"
            type="text"
            placeholder="E. G. Acme Corp"
          />
        </Field>
        <Field>
          <FieldLabel>Secteur / Industrie</FieldLabel>
          <Select
            value={departement}
            onValueChange={(val) => setDepartement(val)}
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
        <Field>
          <FieldLabel>Contact principal</FieldLabel>
          <Input
            id="input-principal-client-name"
            type="text"
            placeholder="Nom complet"
          />
        </Field>
        <Field>
          <FieldLabel>Email</FieldLabel>
          <Input
            id="input-email"
            type="email"
            placeholder="Email@compagnie.com"
          />
        </Field>
      </div>
    </WorkspaceWrapper>
  );
};
