import { z } from "zod";
import { LEVEL_VALUES, OBJECTIVE_VALUES } from "../seed";


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
