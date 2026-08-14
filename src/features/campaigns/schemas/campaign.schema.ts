import { z } from "zod";

export const LEVEL_VALUES = ["Standard", "Elevé", "Urgent"] as const;

export const OBJECTIVE_VALUES = [
  "Génération de prospects",
  "Études de marché",
  "Recherche de partenariats",
] as const;

export const LEVELS = LEVEL_VALUES.map((val) => ({
  label: val,
  value: val,
}));

export const OBJECTIVES = OBJECTIVE_VALUES.map((val) => ({
  label: val,
  value: val,
}));

export const campaignFormSchema = z.object({
  campaignNumber: z
    .string()
    .min(2, "Le nom de la campagne doit faire au moins 2 caractères"),
  objective: z.enum(OBJECTIVE_VALUES, {
    error: "Veuillez choisir un objectif valide",
  }),
  level: z.enum(LEVEL_VALUES, {
    error: "Veuillez choisir un objectif valide",
  }),
});

export type CampaignFormValues = z.infer<typeof campaignFormSchema>;
