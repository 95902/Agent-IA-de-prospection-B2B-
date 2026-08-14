import type { StepsProps } from "../types";
import { Field, FieldDescription, FieldLabel } from "@/components/ui/Field";
import { InfoIcon } from "lucide-react";
import { Textarea } from "@/components/ui/Textarea";
import { Card } from "@/components/ui/Card";
import { WorkspaceWrapper } from "./WorkspaceWrapper";
import { WorkspaceFormSchema3 } from "../schemas/workspace.schema";
import { useForm } from "@tanstack/react-form";

export const WorkspaceForm3 = ({ onNext, onPrevious }: StepsProps) => {
  const form = useForm({
    defaultValues: {
      customerName: "",
      positiveKeywords: "",
      negativeKeywords: "",
    },
    validators: {
      onSubmit: WorkspaceFormSchema3,
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
      title="Affinez le profil de votre client idéal"
      description="Notre IA traitera votre description et vos mots-clés afin de construire un modèle prédictif de notation des prospects."
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 grid-rows-2 gap-4 flex-1">
        <form.Field
          name="customerName"
          children={(field) => (
            <Field className="row-span-2 flex flex-col h-full min-h-0">
              <FieldLabel>Nom du client</FieldLabel>
              <Textarea
                placeholder="Saisissez la description du client..."
                className="flex-1 h-full min-h-0 resize-none"
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={(e) => field.handleChange(e.target.value)}
              />
              <FieldDescription className="text-muted-foreground text-xs mt-1 mb-2 shrink-0">
                Saisissez un ou plusieurs domaines professionnels.
              </FieldDescription>
              <Card className="flex flex-col w-full border rounded-lg gap-2 p-4 shrink-0">
                <div className="flex items-center gap-4">
                  <InfoIcon className="h-5 w-5 shrink-0" />
                  <p className="font-medium">New feature available</p>
                </div>
                <p className="text-muted-foreground text-xs">
                  We&apos;ve added dark mode support. You can enable it in your
                  account settings.
                </p>
              </Card>
            </Field>
          )}
        />
        <form.Field
          name="positiveKeywords"
          children={(field) => (
            <Field className="flex flex-col h-full min-h-0">
              <FieldLabel>Mots clés positifs</FieldLabel>
              <Textarea
                id="input-positive-key"
                placeholder="Ajoutez des mots clés positifs..."
                className="flex-1 h-full min-h-0 resize-none"
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={(e) => field.handleChange(e.target.value)}
              />
            </Field>
          )}
        />
        <form.Field
          name="negativeKeywords"
          children={(field) => (
            <Field className="flex flex-col h-full min-h-0">
              <FieldLabel>Mots clés négatifs</FieldLabel>
              <Textarea
                id="input-negative-key"
                placeholder="Ajoutez des mots clés négatifs..."
                className="flex-1 h-full min-h-0 resize-none"
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={(e) => field.handleChange(e.target.value)}
              />
            </Field>
          )}
        />
      </div>
    </WorkspaceWrapper>
  );
};
