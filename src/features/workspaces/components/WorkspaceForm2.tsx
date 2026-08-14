import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
} from "@/components/ui/Field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import { Input } from "@/components/ui/Input";
import { Progress } from "@/components/ui/Progress";
import { Card } from "@/components/ui/Card";
import type { StepsProps } from "../types";
import { DEPARTEMENTS_VALUES } from "../seed";
import { WorkspaceWrapper } from "./WorkspaceWrapper";
import { useForm } from "@tanstack/react-form";
import { WorkspaceFormSchema2 } from "../schemas/workspace.schema";

export const WorkspaceForm2 = ({ onNext, onPrevious }: StepsProps) => {
  const form = useForm({
    defaultValues: {
      customerName: "",
      code: "",
      numberEmploye: "",
    },
    validators: {
      onSubmit: WorkspaceFormSchema2,
    },
    onSubmit: async ({ value }) => {
      console.log("Données du formulaire soumises :", value);
      onNext();
      // Traitement de l'étape suivante ici
    },
  });

  const handleReset = () => {
    form.reset();
  };

  const handlePrevious = () => {
    onPrevious?.();
  };

  const handleFormSubmit = () => {
    form.handleSubmit();
  };

  return (
    <WorkspaceWrapper
      handleNext={handleFormSubmit}
      handleReset={handleReset}
      handlePrevious={handlePrevious}
      onNext={onNext}
      title="Cible"
      description="Filtrez vos prospects selon la cible choisie"
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 content-start w-full">
        <form.Field
          name="customerName"
          children={(field) => (
            <Field>
              <FieldLabel>Nom du client</FieldLabel>
              <Input
                id="input-client-name"
                type="text"
                placeholder="E. G. Acme Corp"
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={(e) => field.handleChange(e.target.value)}
              />
              {field.state.meta.errors.length > 0 && (
                <FieldError>
                  <p className="text-xs text-red-500">
                    {field.state.meta.errors.length > 0 &&
                      String(field.state.meta.errors[0]?.message)}
                  </p>
                </FieldError>
              )}
              <FieldDescription className="text-muted-foreground text-xs">
                Saisissez un ou plusieurs domaines professionnels.
              </FieldDescription>
            </Field>
          )}
        />
        <form.Field
          name="code"
          children={(field) => (
            <Field>
              <FieldLabel>Codes NAF / SIC</FieldLabel>
              <Input
                id="input-code"
                type="text"
                placeholder="e. g. 6201Z, 7022Z"
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={(e) => field.handleChange(e.target.value)}
              />

              {field.state.meta.errors.length > 0 && (
                <FieldError>
                  <p className="text-xs text-red-500">
                    {field.state.meta.errors.length > 0 &&
                      String(field.state.meta.errors[0]?.message)}
                  </p>
                </FieldError>
              )}
              <FieldDescription className="text-muted-foreground text-xs">
                Saisissez les codes d'activité séparés par des virgules.
              </FieldDescription>
            </Field>
          )}
        />
        <form.Field
          name="numberEmploye"
          children={(field) => (
            <Field>
              <FieldLabel htmlFor="select-naf">Nombre d'employés</FieldLabel>
              <Select
                value={field.state.value}
                onValueChange={(val) => field.handleChange(val ?? "")}
              >
                <SelectTrigger id="select-industry">
                  <SelectValue placeholder="Sélectionnez un secteur ou une industrie" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    {DEPARTEMENTS_VALUES.map((item) => (
                      <SelectItem key={item} value={item}>
                        {item}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
              {field.state.meta.errors.length > 0 && (
                <FieldError>
                  <p className="text-xs text-red-500">
                    {field.state.meta.errors.length > 0 &&
                      String(field.state.meta.errors[0]?.message)}
                  </p>
                </FieldError>
              )}
            </Field>
          )}
        />
        <Card className="p-4 shrink-0 rounded-lg border-2  flex flex-col overflow-hidden">
          <p className="text-blue-500 font-bold">Cible</p>
          <div className="flex flex-col items-center gap-2 w-full">
            <div className="flex justify-between items-center gap-1 w-full">
              <p className="text-lg ">Audience estimé</p>
              <span className="font-bold text-right text-2xl">1240</span>
            </div>
            <Progress
              value={75}
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
