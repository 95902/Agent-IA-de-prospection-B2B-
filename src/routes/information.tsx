/* eslint-disable react-refresh/only-export-components */
import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/Button";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/Field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { Input } from "@/components/ui/Input";

const STEPS = ["Information", "Cible", "Profile ICP", "Confirmation"];

const DEPARTEMENTS = [
  { label: "Engeenering", value: "Engeenering" },
  { label: "Sales", value: "Sales" },
  { label: "BTP", value: "BTP" },
];

const Information = () => {
  const [departement, setDepartement] = useState<string | null>(null);
  const handleReset = () => {
    setDepartement(null);
  };

  return (
    <div className="flex items-center justify-center w-full h-full p-8">
      <div className="w-4/5 h-full flex justify-start gap-8 items-center flex-col">
        <div className="flex flex-col gap-4 items-center justify-center w-full">
          <h1 className="text-3xl font-bold">
            Configurez votre espace de travail
          </h1>
          <h2 className="text-muted-foreground">
            Configurez votre profil client pour aider le moteur d'intelligence
            B2B de ProspectFlow à identifier les prospects à fort potentiel.
          </h2>
        </div>
        <Breadcrumbs data={STEPS} step={0} />
        <div className="p-8 bg-white h-full shrink-0 rounded-lg border-2 min-w-md flex-1 flex flex-col overflow-hidden  w-full">
          <form className="flex flex-col items-end h-full flex-wrap justify-between">
            <FieldGroup>
              <FieldSet>
                <div className="flex items-center justify-between">
                  <div className="flex flex-col">
                    <FieldLegend>
                      <p className="text-3xl font-bold">
                        Information du client
                      </p>
                    </FieldLegend>
                    <FieldDescription>
                      Filtrez vos prospects selon les différents critères
                    </FieldDescription>
                  </div>
                  <Button type="reset" variant="outline" onClick={handleReset}>
                    Réinitialiser
                  </Button>
                </div>
                <FieldGroup>
                  <div className="grid grid-cols-2 gap-4">
                    <Field>
                      <FieldLabel>Nom du client</FieldLabel>
                      <Input
                        id="input-client-name"
                        type="text"
                        placeholder="E. G. Acme Corp"
                      />
                    </Field>
                    <Field>
                      <FieldLabel htmlFor="select-naf">
                        Secteur / Industrie
                      </FieldLabel>
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
                      <FieldLabel>nom du contact principal</FieldLabel>
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
                </FieldGroup>
              </FieldSet>
            </FieldGroup>
            <Button type="submit" className="w-64">
              Suivant <ArrowRight />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/information")({
  component: Information,
});
