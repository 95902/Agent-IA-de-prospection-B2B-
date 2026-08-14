import { Field, FieldError, FieldLabel } from "@/components/ui/Field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import { Input } from "@/components/ui/Input";
import type { StepsProps } from "../types";
import { DEPARTEMENTS_VALUES } from "../seed";
import { WorkspaceWrapper } from "./WorkspaceWrapper";
import { useForm } from "@tanstack/react-form";
import { WorkspaceFormSchema1 } from "../schemas/workspace.schema";

export const WorkspaceForm1 = ({ onNext }: StepsProps) => {
  const form = useForm({
    defaultValues: {
      customerName: "",
      industry: "",
      contact: "",
      email: "",
    },
    validators: {
      onSubmit: WorkspaceFormSchema1,
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
  const handleFormSubmit = () => {
    form.handleSubmit();
  };

  return (
    <WorkspaceWrapper
      handleNext={handleFormSubmit}
      handleReset={handleReset}
      onNext={onNext}
      title="Information du client"
      description="Filtrez vos prospects selon les différents critères"
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
                    {field.state.meta.errors[0]?.message ??
                      String(field.state.meta.errors[0])}
                  </p>
                </FieldError>
              )}
            </Field>
          )}
        />
        <form.Field
          name="industry"
          children={(field) => (
            <Field>
              <FieldLabel>Secteur / Industrie</FieldLabel>
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
                    {field.state.meta.errors[0]?.message ??
                      String(field.state.meta.errors[0])}
                  </p>
                </FieldError>
              )}
            </Field>
          )}
        />
        <form.Field
          name="contact"
          children={(field) => (
            <Field>
              <FieldLabel>Contact principal</FieldLabel>
              <Input
                id="input-principal-client-name"
                type="text"
                placeholder="Nom complet"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
              />
              {field.state.meta.errors.length > 0 && (
                <FieldError>
                  <p className="text-xs text-red-500">
                    {field.state.meta.errors[0]?.message ??
                      String(field.state.meta.errors[0])}
                  </p>
                </FieldError>
              )}
            </Field>
          )}
        />
        <form.Field
          name="email"
          children={(field) => (
            <Field>
              <FieldLabel>Email</FieldLabel>
              <Input
                id="input-email"
                type="email"
                placeholder="Email@compagnie.com"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
              />
              {field.state.meta.errors.length > 0 && (
                <FieldError>
                  <p className="text-xs text-red-500">
                    {field.state.meta.errors[0]?.message ??
                      String(field.state.meta.errors[0])}
                  </p>
                </FieldError>
              )}
            </Field>
          )}
        />
      </div>
    </WorkspaceWrapper>
  );
};
