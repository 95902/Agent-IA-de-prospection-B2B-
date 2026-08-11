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
import { useState, type SubmitEvent, type MouseEvent } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CircleMinus,
  Flame,
  InfoIcon,
  Mail,
  Settings,
  UserSearch,
} from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Progress } from "@/components/ui/Progress";
import { Textarea } from "@/components/ui/Textarea";
import type { BaseUIEvent } from "@base-ui/react/types";
import Tower from "@/assets/tower.png";
import { Switch } from "@/components/ui/Switch";
import { Card } from "@/components/ui/Card";

const STEPS = ["Information", "Cible", "Profile ICP", "Confirmation"];

const DEPARTEMENTS = [
  { label: "Engeenering", value: "Engeenering" },
  { label: "Sales", value: "Sales" },
  { label: "BTP", value: "BTP" },
];

interface StepsProps {
  onNext: () => void;
  onPrevious?: () => void;
}

const Step4 = ({ onPrevious }: StepsProps) => {
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

const Step3 = ({ onNext, onPrevious }: StepsProps) => {
  const handleReset = () => {};

  const handleNext = (e: SubmitEvent) => {
    e.preventDefault();
    onNext();
  };

  const handlePrevious = (e: BaseUIEvent<MouseEvent<HTMLButtonElement>>) => {
    e.preventDefault();
    onPrevious?.();
  };

  return (
      <form
        onSubmit={handleNext}
        className="flex flex-col h-full justify-between gap-6"
      >
        <FieldGroup className="flex-1 flex flex-col min-h-0">
          <FieldSet className="flex-1 flex flex-col min-h-0">
            <div className="flex  justify-between pb-4">
              <div className="flex flex-col">
                <FieldLegend>
                  <p className="text-3xl font-bold">
                    Affinez le profil de votre client idéal
                  </p>
                </FieldLegend>
                <FieldDescription className="max-w-4/5">
                  Notre IA traitera votre description et vos mots-clés afin de
                  construire un modèle prédictif de notation des prospects.
                </FieldDescription>
              </div>
              <Button type="reset" variant="outline" onClick={handleReset}>
                Réinitialiser
              </Button>
            </div>

            <div className="grid grid-cols-2 grid-rows-2 gap-4 flex-1 min-h-0">
              <Field className="row-span-2 flex flex-col h-full min-h-0">
                <FieldLabel>Nom du client</FieldLabel>
                <Textarea
                  placeholder="Saisissez la description du client..."
                  className="flex-1 resize-none"
                />
                <FieldDescription className="text-muted-foreground text-xs mt-1 mb-2">
                  Saisissez un ou plusieurs domaines professionnels.
                </FieldDescription>
                <Card className="flex flex-col w-full border rounded-lg gap-2 p-4">
                  <div className="flex items-center gap-4">
                    <InfoIcon />
                    <p>New feature available</p>
                  </div>
                  <p className="text-muted-foreground text-xs">
                    We&apos;ve added dark mode support. You can enable it in
                    your account settings.
                  </p>
                </Card>
              </Field>
              <Field className="flex flex-col h-full min-h-0">
                <FieldLabel>Mots clés positifs</FieldLabel>
                <Textarea
                  id="input-positive-key"
                  placeholder="Ajoutez des mots clés positifs..."
                  className="flex-1 resize-none"
                />
              </Field>
              <Field className="flex flex-col h-full min-h-0">
                <FieldLabel>Mots clés négatifs</FieldLabel>
                <Textarea
                  id="input-negative-key"
                  placeholder="Ajoutez des mots clés négatifs..."
                  className="flex-1 resize-none"
                />
              </Field>
            </div>
          </FieldSet>
        </FieldGroup>

        <div className="flex w-full justify-between items-center pt-4">
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
      </form>
  );
};

const Step2 = ({ onNext, onPrevious }: StepsProps) => {
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
      <form
        onSubmit={handleNext}
        className="flex flex-col items-end h-full gap-4 lg:flex-wrap justify-between"
      >
        <FieldGroup>
          <FieldSet>
            <div className="flex flex-col gap-4 lg:flex-row justify-between">
              <div className="flex flex-col">
                <FieldLegend>
                  <p className="text-3xl font-bold">Cible </p>
                </FieldLegend>
                <FieldDescription>
                  Filtrez vos prospects selon la cible choisie
                </FieldDescription>
              </div>
              <Button type="reset" variant="outline" className="w-fit" onClick={handleReset}>
                Réinitialiser
              </Button>
            </div>
            <FieldGroup>
              <div className="grid lg:grid-cols-2 gap-4">
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
                  <FieldLabel htmlFor="select-naf">
                    Nombre d'employés
                  </FieldLabel>
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
                      <span className="font-bold text-right text-2xl">
                        1240
                      </span>
                    </div>
                    <Progress
                      value={audience}
                      className="w-full shrink-0"
                      indicatorClassName="bg-green-500"
                    />
                    <p className="text-xs text-muted-foreground">
                      Vos filtres actuels correspondent à 65 % du pool total
                      disponible dans cette région.
                    </p>
                  </div>
                </Card>
              </div>
            </FieldGroup>
          </FieldSet>
        </FieldGroup>
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
      </form>
  );
};

const Step1 = ({ onNext }: StepsProps) => {
  const [departement, setDepartement] = useState<string | null>(null);
  const handleReset = () => {
    setDepartement(null);
  };

  const handleNext = (e: SubmitEvent) => {
    e.preventDefault();
    onNext();
  };

  return (
    <form
      onSubmit={handleNext}
      className="flex flex-col items-end flex-wrap h-full justify-between"
    >
      <FieldGroup>
        <FieldSet>
          <div className="flex flex-col h-full lg:flex-row justify-between gap-4">
            <div className="flex flex-col">
              <FieldLegend>
                <p className="text-3xl font-bold text-nowrap">
                  Information du client
                </p>
              </FieldLegend>
              <FieldDescription>
                Filtrez vos prospects selon les différents critères
              </FieldDescription>
            </div>
            <Button
              type="reset"
              variant="outline"
              className="w-fit"
              onClick={handleReset}
            >
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
          </FieldGroup>
        </FieldSet>
      </FieldGroup>
      <Button type="submit" className="w-fit">
        Suivant <ArrowRight />
      </Button>
    </form>
  );
};

const Workspace = () => {
  const [step, setStep] = useState<number>(0);

  const handleNext = () => {
    setStep((prev) => Math.min(prev + 1, STEPS.length - 1));
  };

  const handlePrevious = () => {
    setStep((prev) => Math.max(prev - 1, 0));
  };

  const handleSubmit = () => {};

  return (
    <div className="flex flex-col items-center gap-8 justify-center w-full h-full">
      <Breadcrumbs data={STEPS} step={step} />

      {step === 3 ? (
        <Step4 onNext={handleSubmit} onPrevious={handlePrevious} />
      ) : (
        <div className="w-full h-full flex flex-col justify-start gap-8 items-center">
          <div className="flex flex-col gap-4 items-center justify-center w-full">
            <h1 className="text-3xl font-bold">
              Configurez votre espace de travail
            </h1>
            <h2 className="text-muted-foreground">
              Configurez votre profil client pour aider le moteur d'intelligence
              B2B de ProspectFlow à identifier les prospects à fort potentiel.
            </h2>
          </div>
          <Card className="rounded-lg border-2 flex-1 flex flex-col overflow-y-scroll w-full h-full p-4 ">
            {step === 0 && <Step1 onNext={handleNext} />}
            {step === 1 && (
              <Step2 onNext={handleNext} onPrevious={handlePrevious} />
            )}
            {step === 2 && (
              <Step3 onNext={handleNext} onPrevious={handlePrevious} />
            )}
            {step === 3 && (
              <Step4 onNext={handleSubmit} onPrevious={handlePrevious} />
            )}
          </Card>
        </div>
      )}
    </div>
  );
};

export const Route = createFileRoute("/workspace")({
  component: Workspace,
});
