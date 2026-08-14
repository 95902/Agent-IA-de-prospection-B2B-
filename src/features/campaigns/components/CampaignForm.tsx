import { Button } from "@/components/ui/Button";
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
import { Card } from "@/components/ui/Card";
import { campaignFormSchema } from "@/features/campaigns/schemas/campaign.schema";
import { useForm } from "@tanstack/react-form";
import { LEVEL_VALUES, OBJECTIVE_VALUES } from "../seed";

export const CampaignForm = () => {
  const form = useForm({
    defaultValues: {
      campaignNumber: "",
      objective: "",
      level: "",
    },
    validators: {
      onSubmit: campaignFormSchema,
    },
    onSubmit: async ({ value }) => {
      console.log("Données du formulaire soumises :", value);
      // Traitement de l'étape suivante ici
    },
  });

  return (
    <Card className="min-w-full h-fit overflow-hidden border rounded-lg p-4 shrink-0">
      <form
        className="flex flex-col gap-6 justify-between items-end"
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          form.handleSubmit();
        }}
      >
        <form.Field
          name="campaignNumber"
          children={(field) => (
            <Field>
              <FieldLabel>Numéro de la Campagne</FieldLabel>
              <Input
                id="campaign-name"
                type="text"
                className="w-full rounded-lg border"
                placeholder="Saas Founders Expansion"
                value={field.state.value}
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

        <div className="flex gap-4 w-full">
          <form.Field
            name="objective"
            children={(field) => (
              <Field>
                <FieldLabel>Objectif</FieldLabel>
                <Select
                  value={field.state.value}
                  onValueChange={(val) => field.handleChange(val ?? "")}
                >
                  <SelectTrigger
                    id="select-objective"
                    className="w-full rounded-lg border"
                  >
                    <SelectValue placeholder="Objectif" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      {OBJECTIVE_VALUES.map((item) => (
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
            name="level"
            children={(field) => (
              <Field>
                <FieldLabel htmlFor="select-level">Niveau</FieldLabel>
                <Select
                  value={field.state.value}
                  onValueChange={(val) => field.handleChange(val ?? "")}
                >
                  <SelectTrigger
                    id="select-level"
                    className="w-full rounded-lg border"
                  >
                    <SelectValue placeholder="Niveau" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      {LEVEL_VALUES.map((item) => (
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
        </div>
        <Button type="submit" className="w-fit">
          Prochaine étape
        </Button>
      </form>
    </Card>
  );
};
