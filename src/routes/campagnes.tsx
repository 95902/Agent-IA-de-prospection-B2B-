/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/Button";
import { Field, FieldGroup, FieldLabel, FieldSet } from "@/components/ui/Field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import { Input } from "@/components/ui/Input";
import React, { useState } from "react";
import { Progress } from "@/components/ui/Progress";
import { CircleAlert, CircleCheck, TrendingUp } from "lucide-react";
import image from "@/assets/Image.png";
const LEVELS = [
  { label: "Standard", value: "Standard" },
  { label: "Elevé", value: "Elevé" },
  { label: "Urgent", value: "Urgent" },
];

const OBJECTIVES = [
  { label: "Génération de prospects", value: "Génération de prospects" },
  { label: "Études de marché", value: "Études de marché" },
  { label: "Recherche de partenariats", value: "Recherche de partenariats" },
];

const SCORING_STATUS = 25;

const BREADCRUMBS = ["INFORMATIONS", "CIBLE", "MOTS CLEF"];

function Campaigns() {
  const [objective, setObjective] = useState<string | null>(null);
  const [level, setLevel] = useState<string | null>(null);
  return (
    <div className="w-full h-full flex gap-4 ">
      <div className="flex flex-col gap-6 flex-1">
        <h1 className="text-2xl font-bold">Création de campagne</h1>
        <h2 className="text-sm text-muted-foreground pb-4">
          Configurez vos paramètres de ciblage et de prospection pour commencer
          à trouver des prospects qualifiés.
        </h2>
        <div className="flex gap-2 w-full items-center ">
          {BREADCRUMBS.map((crumb, index) => {
            const isLast = index === BREADCRUMBS.length - 1;
            return (
              <React.Fragment key={index}>
                <div className="min-w-8 min-h-8 rounded-full bg-blue-500 shrink-0 items-center justify-center flex text-white">
                  {index}
                </div>
                <p className="text-blue-500 whitespace-nowrap shrink-0">
                  {crumb}
                </p>
                {!isLast && (
                  <div className="w-full min-h-1 bg-blue-500 rounded-lg" />
                )}
              </React.Fragment>
            );
          })}
        </div>
        <div className="w-full gap-4 flex flex-1">
          <div className="w-full min-w-md h-fit overflow-hidden border rounded-lg p-4 bg-white shrink-0">
            <form className="flex flex-col gap-6 justify-between items-end ">
              <FieldGroup>
                <FieldSet>
                  <FieldGroup>
                    <Field>
                      <FieldLabel htmlFor="checkout-7j9-card-number-uw1">
                        Numéro de la Campagne
                      </FieldLabel>
                      <Input
                        id="input-demo-api-key"
                        type="password"
                        className="w-full rounded-lg border"
                        placeholder="Saas Founders Expansion"
                      />
                    </Field>
                    <div className="flex gap-4 w-full">
                      <Field>
                        <FieldLabel htmlFor="select-objective">
                          Objectif
                        </FieldLabel>
                        <Select
                          value={objective}
                          onValueChange={(val) => setObjective(val)}
                        >
                          <SelectTrigger
                            id="select-objective"
                            className="w-full rounded-lg border"
                          >
                            <SelectValue placeholder="Objectif" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectGroup>
                              {OBJECTIVES.map((item) => (
                                <SelectItem key={item.value} value={item.value}>
                                  {item.label}
                                </SelectItem>
                              ))}
                            </SelectGroup>
                          </SelectContent>
                        </Select>
                      </Field>
                      <Field>
                        <FieldLabel htmlFor="select-level">Niveau</FieldLabel>
                        <Select
                          value={level}
                          onValueChange={(val) => setLevel(val)}
                        >
                          <SelectTrigger
                            id="select-level"
                            className="w-full rounded-lg border"
                          >
                            <SelectValue placeholder="Niveau" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectGroup>
                              {LEVELS.map((item) => (
                                <SelectItem key={item.value} value={item.value}>
                                  {item.label}
                                </SelectItem>
                              ))}
                            </SelectGroup>
                          </SelectContent>
                        </Select>
                      </Field>
                    </div>
                  </FieldGroup>
                </FieldSet>
              </FieldGroup>
              <Button type="submit" className="w-64 rounded-md bg-blue-500">
                Prochaine étape
              </Button>
            </form>
          </div>
        </div>
      </div>
      <div className="flex flex-col gap-4 h-full min-w-md">
        <div className="max-w-md w-full border overflow-hidden rounded-xl bg-white shrink-0">
          <div className="flex flex-col gap-4 border-b rounded-t-lg p-8 bg-[#C6C6CD]/20">
            <p>Estimations en direct</p>
            <p>
              <span className="font-bold text-5xl  text-blue-700">2482 </span>
              Prospects
            </p>
          </div>
          <div className="flex flex-col gap-6 p-8 w-full">
            <div className="flex flex-col items-center gap-2 w-full">
              <div className="flex justify-between items-center gap-1 w-full">
                <p className="text-xs font-bold">Précision du profil</p>
                <span className="font-bold w-6 text-right text-xs text-green-500">
                  {SCORING_STATUS}%
                </span>
              </div>
              <Progress
                value={SCORING_STATUS}
                className="w-full shrink-0"
                indicatorClassName="bg-green-500"
              />
            </div>
            <div className="flex flex-col items-center gap-2 w-full">
              <div className="flex items-center gap-2 w-full">
                <CircleCheck color="green" />
                <p>Email vérifié</p>
              </div>
              <div className="flex items-center gap-2 w-full">
                <CircleCheck color="green" />
                <p>téléphone valide</p>
              </div>
              <div className="flex items-center gap-2 w-full">
                <CircleCheck color="green" />
                <p>Profil linkedin lié</p>
              </div>
            </div>
          </div>
          <div className="border w-[90%] mx-4" />
          <div className="flex  gap-2 items-center  p-8 ">
            <CircleAlert />
            <p className="text-sm text-muted-foreground">
              Données mises à jour il y a 2 minutes
            </p>
          </div>
        </div>
        <div className="flex-1 flex flex-col max-w-md border-2 gap-6 overflow-hidden rounded-lg p-8 shrink-0 bg-[#C6C6CD]/20">
          <div className="flex items-center gap-2">
            <TrendingUp />
            <p>Estimations en direct</p>
          </div>
          <img src={image} alt="Description" />
          <p className="text-sm text-muted-foreground text-wrap">
            Les entreprises SaaS de votre région sélectionnée constatent
            actuellement une augmentation de 15 % des embauches pour les postes
            d'ingénierie.
          </p>
        </div>
      </div>
    </div>
  );
}

export const Route = createFileRoute("/campagnes")({
  component: Campaigns,
});
